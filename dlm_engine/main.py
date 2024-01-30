import logging
import random
import string
import sys
import time

from authlib.integrations.starlette_client import OAuth
import bonsai.asyncio
import httpx
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi_versionizer import Versionizer
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.sessions import SessionMiddleware

import dlm_engine.api
import dlm_engine.oauth

from dlm_engine.authorize import Authorize

from dlm_engine.config import Settings
from dlm_engine.config import OAuth as SettingsOAuth
from dlm_engine.config import Ldap as SettingsLdap

from dlm_engine.crud.credentials import CrudCredentials
from dlm_engine.crud.ldap import CrudLdap
from dlm_engine.crud.oauth import CrudOAuthGitHub
from dlm_engine.crud.orgs import CrudOrgs
from dlm_engine.crud.orgs_teams import CrudOrgsTeams
from dlm_engine.crud.orgs_locks import CrudOrgsLocks
from dlm_engine.crud.users import CrudUsers

from dlm_engine.errors import ResourceNotFound

from dlm_engine.model.users import UserPost

settings = Settings(_env_file=".env")

app = FastAPI(title="dlm_engine", version="0.0.0")
app.add_middleware(
    SessionMiddleware, secret_key=settings.app.secretkey, max_age=3600
)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup_event():
    log = setup_logging(settings.app.loglevel)
    log.info(settings)

    http = httpx.AsyncClient()

    ldap_settings = settings.ldap
    ldap_pool = setup_ldap(log=log, ldap_settings=ldap_settings)
    if ldap_pool:
        await ldap_pool.open()

    log.info("adding routes")
    mongo_db = setup_mongodb(
        log=log, database=settings.mongodb.database, url=settings.mongodb.url
    )

    oauth_providers = setup_oauth_providers(
        log=log, http=http, oauth_settings=settings.oauth
    )

    crud_ldap = CrudLdap(log=log, pool=ldap_pool)

    crud_orgs = CrudOrgs(log=log, coll=mongo_db["orgs"])
    await crud_orgs.index_create()

    crud_orgs_teams = CrudOrgsTeams(log=log, coll=mongo_db["orgs_teams"])
    await crud_orgs_teams.index_create()

    crud_orgs_packages = CrudOrgsLocks(log=log, coll=mongo_db["packages"])
    await crud_orgs_packages.index_create()

    crud_users = CrudUsers(log=log, coll=mongo_db["users"])
    await crud_users.index_create()

    crud_users_credentials = CrudCredentials(
        log=log, coll=mongo_db["users_credentials"]
    )
    await crud_users_credentials.index_create()

    authorize = Authorize(
        log=log,
        crud_orgs_teams=crud_orgs_teams,
        crud_users=crud_users,
    )

    api_router = dlm_engine.api.Api(
        log=log,
        authorize=authorize,
        crud_ldap=crud_ldap,
        crud_orgs=crud_orgs,
        crud_orgs_teams=crud_orgs_teams,
        crud_orgs_packages=crud_orgs_packages,
        crud_users=crud_users,
        crud_users_credentials=crud_users_credentials,
        http=http,
    )
    app.include_router(api_router.router)
    Versionizer(
        app=app,
        prefix_format="/api/v{major}",
        include_versions_route=True,
        semantic_version_format='{major}',
    ).versionize()

    oauth_router = dlm_engine.oauth.Oauth(
        log=log, crud_users=crud_users, http=http, oauth_providers=oauth_providers
    )
    app.include_router(oauth_router.router)

    log.info("adding routes, done")
    await setup_admin_user(log=log, crud_users=crud_users)


async def setup_admin_user(log: logging.Logger, crud_users: CrudUsers):
    try:
        await crud_users.get(_id="admin", fields=["_id"])
    except ResourceNotFound:
        # create random password
        password = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(20)
        )
        log.info(f"creating admin user with password {password}")
        await crud_users.create(
            _id="admin",
            payload=UserPost(
                admin=True,
                email="admin@example.com",
                name="admin",
                password=password,
            ),
            fields=["_id", "admin", "email", "name"],
        )
        log.info(f"creating admin user, done")


def setup_ldap(log: logging.Logger, ldap_settings: SettingsLdap):
    if not ldap_settings.url:
        log.info("ldap not configured")
        return
    log.info(f"setting up ldap with {ldap_settings.url} as a backend")
    if not ldap_settings.binddn:
        log.fatal("ldap binddn not configured")
        sys.exit(1)
    if not ldap_settings.password:
        log.fatal("ldap password not configured")
        sys.exit(1)
    client = bonsai.LDAPClient(ldap_settings.url)
    client.set_credentials("SIMPLE", ldap_settings.binddn, ldap_settings.password)
    pool = bonsai.asyncio.AIOConnectionPool(client=client, maxconn=30)
    return pool


def setup_logging(log_level):
    log = logging.getLogger("uvicorn")
    log.info(f"setting loglevel to: {log_level}")
    log.setLevel(log_level)
    return log


def setup_mongodb(log: logging.Logger, database: str, url: str) -> AsyncIOMotorClient:
    log.info("setting up mongodb client")
    pool = AsyncIOMotorClient(url)
    db = pool.get_database(database)
    log.info("setting up mongodb client, done")
    return db


def setup_oauth_providers(
    log: logging.Logger,
    http: httpx.AsyncClient,
    oauth_settings: dict["str", SettingsOAuth],
):
    oauth = OAuth()
    providers = {}
    for provider, config in oauth_settings.items():
        if config.type == "github":
            log.info(f"oauth setting up github provider with name {provider}")
            providers[provider] = CrudOAuthGitHub(
                log=log,
                http=http,
                name=provider,
                oauth=oauth,
                scope=config.scope,
                client_id=config.client.id,
                client_secret=config.client.secret,
                authorize_url=config.url.authorize,
                access_token_url=config.url.accesstoken,
                userinfo_url=config.url.userinfo,
            )
    return providers
