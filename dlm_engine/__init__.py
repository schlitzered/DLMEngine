import argparse
import asyncio
import configparser
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import time

from aiohttp import web
import jsonschema
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

from dlm_engine.controller.authenticate import Authenticate as ControllerAuthenticate
from dlm_engine.controller.locks import Locks as ControllerLocks
from dlm_engine.controller.permissions import Permissions as ControllerPermissions
from dlm_engine.controller.users import Users as ControllerUsers
from dlm_engine.controller.users import UsersCredentials as ControllerUsersCredentials

from dlm_engine.errors import DuplicateResource

from dlm_engine.middleware import request_id, error_catcher

from dlm_engine.models.aa import AuthenticationAuthorization as ModelAuthenticationAuthorization
from dlm_engine.models.credentials import Credentials as ModelCredentials
from dlm_engine.models.locks import Locks as ModelLocks
from dlm_engine.models.permissions import Permissions as ModelPermissions
from dlm_engine.models.sessions import Sessions as ModelSessions
from dlm_engine.models.users import Users as ModelUsers

from dlm_engine.schemes.config_main import CHECK_CONFIG_MAIN
from dlm_engine.schemes.config_main import CHECK_CONFIG_MONGOCOLL, CHECK_CONFIG_MONGOPOOL
from dlm_engine.schemes.config_main import CHECK_CONFIG_REDISPOOL


def main():
    parser = argparse.ArgumentParser(description="DLMEngine Rest API")

    parser.add_argument("--cfg", dest="cfg", action="store",
                        default="/etc/dlm_engine/dlm_engine.ini",
                        help="Full path to configuration")

    subparsers = parser.add_subparsers(help='commands', dest='method')
    subparsers.required = True

    run_parser = subparsers.add_parser('run', help='Start DLMEngine Rest API API')
    run_parser.set_defaults(method='run')

    indicies_parser = subparsers.add_parser('indices', help='create indices and exit')
    indicies_parser.set_defaults(method='indices')

    admin_parser = subparsers.add_parser('create_admin', help='create default admin user')
    admin_parser.set_defaults(method='create_admin')

    parsed_args = parser.parse_args()

    dlm_engine_restapi = DLMEngineRest(
        cfg=parsed_args.cfg,
    )

    if parsed_args.method == 'run':
        dlm_engine_restapi.run()

    elif parsed_args.method == 'indices':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(dlm_engine_restapi.manage_indices())
        loop.close()

    elif parsed_args.method == 'create_admin':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(dlm_engine_restapi.create_admin())
        loop.close()


class DLMEngineRest:
    def __init__(self, cfg):
        self._config_file = cfg
        self._config = configparser.ConfigParser()
        self._config_dict = None
        self._mongo_pools = dict()
        self._mongo_colls = dict()
        self.log = logging.getLogger('application')
        self.config.read_file(open(self._config_file))
        self._config_dict = self._cfg_to_dict(self.config)
        try:
            jsonschema.validate(self.config_dict['main'], CHECK_CONFIG_MAIN)
        except jsonschema.exceptions.ValidationError as err:
            print("main section: {0}".format(err))
            sys.exit(1)

    def _acc_logging(self):
        acc_handlers = []
        access_log = self.config.get('file:logging', 'acc_log')
        access_retention = self.config.getint('file:logging', 'acc_retention')
        acc_handlers.append(TimedRotatingFileHandler(access_log, 'D', 1, access_retention))
        return acc_handlers

    def _app_logging(self):
        logfmt = logging.Formatter('%(asctime)sUTC - %(levelname)s - %(message)s')
        logfmt.converter = time.gmtime
        app_handlers = []
        aap_level = self.config.get('file:logging', 'app_loglevel')
        app_log = self.config.get('file:logging', 'app_log')
        app_retention = self.config.getint('file:logging', 'app_retention')
        app_handlers.append(TimedRotatingFileHandler(app_log, 'd', 1, app_retention))

        for handler in app_handlers:
            handler.setFormatter(logfmt)
            self.log.addHandler(handler)
        self.log.setLevel(aap_level)
        self.log.debug("application logger is up")

    def run(self):
        self._app_logging()
        self.log.info("starting up")
        self._setup_mongo_pools()
        self._setup_mongo_colls()
        self._validate_redis_pools()

        m_locks = ModelLocks(self._mongo_colls['locks'])
        m_permissions = ModelPermissions(self._mongo_colls['permissions'])
        m_sessions = ModelSessions(
            self.config.get('session:redispool', 'host', fallback='127.0.0.1'),
            self.config.get('session:redispool', 'port', fallback=6379),
            self.config.get('session:redispool', 'pass', fallback=None)
        )
        m_users = ModelUsers(self._mongo_colls['users'])
        m_users_cred = ModelCredentials(self._mongo_colls['users_credentials'])
        m_aa = ModelAuthenticationAuthorization(
            users=m_users,
            users_credentials=m_users_cred,
            permissions=m_permissions,
            sessions=m_sessions
        )

        c_authenticate = ControllerAuthenticate(sessions=m_sessions, users=m_users)
        c_locks = ControllerLocks(
            aa=m_aa, locks=m_locks)
        c_permissions = ControllerPermissions(
            aa=m_aa, permissions=m_permissions, users=m_users
        )
        c_user = ControllerUsers(
            aa=m_aa, credentials=m_users_cred,
            permissions=m_permissions, users=m_users
        )
        c_user_cred = ControllerUsersCredentials(
            aa=m_aa, credentials=m_users_cred, users=m_users
        )

        app = web.Application(middlewares=[request_id, error_catcher])

        app.router.add_static('/static/', path=str('{0}/static'.format(os.path.dirname(__file__))))

        app.router.add_route('DELETE', '/api/v1/authenticate', c_authenticate.delete)
        app.router.add_route('GET', '/api/v1/authenticate', c_authenticate.get)
        app.router.add_route('POST', '/api/v1/authenticate', c_authenticate.post)

        app.router.add_route('GET', '/api/v1/locks/_search', c_locks.search)
        app.router.add_route('DELETE', '/api/v1/locks/{lock}', c_locks.delete)
        app.router.add_route('GET', '/api/v1/locks/{lock}', c_locks.get)
        app.router.add_route('POST', '/api/v1/locks/{lock}', c_locks.post)

        app.router.add_route('GET', '/api/v1/permissions/_search', c_permissions.search)
        app.router.add_route('DELETE', '/api/v1/permissions/{perm}', c_permissions.delete)
        app.router.add_route('GET', '/api/v1/permissions/{perm}', c_permissions.get)
        app.router.add_route('POST', '/api/v1/permissions/{perm}', c_permissions.post)
        app.router.add_route('PUT', '/api/v1/permissions/{perm}', c_permissions.put)

        app.router.add_route('GET', '/api/v1/users/_search', c_user.search)
        app.router.add_route('DELETE', '/api/v1/users/{user}', c_user.delete)
        app.router.add_route('GET', '/api/v1/users/{user}', c_user.get)
        app.router.add_route('POST', '/api/v1/users/{user}', c_user.post)
        app.router.add_route('PUT', '/api/v1/users/{user}', c_user.put)

        app.router.add_route('GET', '/api/v1/users/{user}/credentials', c_user_cred.get_all)
        app.router.add_route('DELETE', '/api/v1/users/{user}/credentials/{cred}', c_user_cred.delete)
        app.router.add_route('GET', '/api/v1/users/{user}/credentials/{cred}', c_user_cred.get)
        app.router.add_route('POST', '/api/v1/users/{user}/credentials', c_user_cred.post)
        app.router.add_route('PUT', '/api/v1/users/{user}/credentials/{cred}', c_user_cred.put)

        web.run_app(
            app=app,
            host=self.config.get('main', 'host'),
            port=self.config.getint('main', 'port'),
            access_log=self.log
        )

        self.log.info("shutting down")

    @staticmethod
    def _cfg_to_dict(config):
        result = {}
        for section in config.sections():
            result[section] = {}
            for option in config.options(section):
                try:
                    result[section][option] = config.getint(section, option)
                    continue
                except ValueError:
                    pass
                try:
                    result[section][option] = config.getfloat(section, option)
                    continue
                except ValueError:
                    pass
                try:
                    result[section][option] = config.getboolean(section, option)
                    continue
                except ValueError:
                    pass
                try:
                    result[section][option] = config.get(section, option)
                    continue
                except ValueError:
                    pass
        return result

    def _setup_mongo_pools(self):
        self.log.info("setting up mongodb connection pools")
        for section in self.config.sections():
            if section.endswith(':mongopool'):
                try:
                    jsonschema.validate(self.config_dict[section], CHECK_CONFIG_MONGOPOOL)
                except jsonschema.exceptions.ValidationError as err:
                    print("{0} section: {1}".format(section, err))
                    sys.exit(1)
                sectionname = section.rsplit(':', 1)[0]
                self.log.debug("setting up mongodb connection pool {0}".format(sectionname))
                pool = AsyncIOMotorClient(
                    host=self.config.get(section, 'hosts'),
                )
                db = pool.get_database(self.config.get(section, 'db'))
                try:
                    user = self.config.get(section, 'user')
                    password = self.config.get(section, 'pass')
                    db.authenticate(user, password)
                    self.log.debug("connection pool {0} is using authentication".format(sectionname))
                except configparser.NoOptionError:
                    self.log.debug("connection pool {0} is not using authentication".format(sectionname))
                self._mongo_pools[sectionname] = db
                self.log.debug("setting up mongodb connection pool {0} done".format(sectionname))
        self.log.info("setting up mongodb connection pools done")

    def _setup_mongo_colls(self):
        self.log.info("setting up mongodb collections")
        for section in self.config.sections():
            if section.endswith(':mongocoll'):
                try:
                    jsonschema.validate(self.config_dict[section], CHECK_CONFIG_MONGOCOLL)
                except jsonschema.exceptions.ValidationError as err:
                    print("{0} section: {1}".format(section, err))
                    sys.exit(1)
                sectionname = section.rsplit(':', 1)[0]
                self.log.debug("setting up mongodb collection {0}".format(sectionname))
                pool_name = self.config.get(section, 'pool')
                coll_name = self.config.get(section, 'coll')
                self.log.debug("mongodb collection {0} is using mongodb connection pool {1}"
                               .format(sectionname, pool_name))
                self.log.debug("mongodb collection {0} is using collection name {1}".format(sectionname, coll_name))
                pool = self._mongo_pools[pool_name]
                coll = pool.get_collection(coll_name)
                self._mongo_colls[sectionname] = coll
                self.log.debug("setting up mongodb collection {0} done".format(sectionname))
        self.log.info("setting up mongodb collections done")

    def _validate_redis_pools(self):
        self.log.info("setting up redis pools")
        for section in self.config.sections():
            if section.endswith(':redispool'):
                try:
                    jsonschema.validate(self.config_dict[section], CHECK_CONFIG_REDISPOOL)
                except jsonschema.exceptions.ValidationError as err:
                    print("{0} section: {1}".format(section, err))
                    sys.exit(1)
        self.log.info("setting up redis pools done")

    @property
    def config(self):
        return self._config

    @property
    def config_dict(self):
        return self._config_dict

    async def create_admin(self):
        self.config.read_file(open(self._config_file))
        self._config_dict = self._cfg_to_dict(self.config)
        self._setup_mongo_pools()
        self._setup_mongo_colls()

        admin = {
            "admin": True,
            "backend": "internal",
            "backend_ref": "default_admin",
            "email": "default_admin@internal",
            "name": "Default Admin User",
            "password": "password"
        }
        try:
            print("creating admin user...")
            m_users = ModelUsers(self._mongo_colls['users'])
            await m_users.create('admin', admin)
            print("done...")
        except DuplicateResource:
            print("admin user already exists...")

    async def manage_indices(self):
        self.config.read_file(open(self._config_file))
        self._config_dict = self._cfg_to_dict(self.config)
        self._setup_mongo_pools()
        self._setup_mongo_colls()

        c_locks = self._mongo_colls["locks"]
        await c_locks.create_index([
            ("id", pymongo.ASCENDING)
        ], unique=True)
        c_permissions = self._mongo_colls["permissions"]
        await c_permissions.create_index([
            ("id", pymongo.ASCENDING)
        ], unique=True)
        await c_permissions.create_index([
            ("permissions", pymongo.ASCENDING),
        ])
        await c_permissions.create_index([
            ("users", pymongo.ASCENDING),
        ])
        c_users = self._mongo_colls["users"]
        await c_users.create_index([
            ("id", pymongo.ASCENDING)
        ], unique=True)

        c_users_credentials = self._mongo_colls["users_credentials"]
        await c_users_credentials.create_index([
            ("id", pymongo.ASCENDING),
            ("owner", pymongo.ASCENDING)
        ], unique=True)

