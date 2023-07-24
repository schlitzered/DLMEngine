import logging

import httpx
from fastapi import APIRouter

from dlm_engine.authorize import Authorize

from dlm_engine.api.authenticate import ApiAuthenticate
from dlm_engine.api.orgs_teams import ApiOrgsTeams
from dlm_engine.api.orgs import ApiOrgs
from dlm_engine.api.orgs_locks import ApiOrgsLocks
from dlm_engine.api.users import ApiUsers
from dlm_engine.api.users_credentials import ApiUsersCredentials

from dlm_engine.crud.credentials import CrudCredentials
from dlm_engine.crud.ldap import CrudLdap
from dlm_engine.crud.orgs import CrudOrgs
from dlm_engine.crud.orgs_teams import CrudOrgsTeams
from dlm_engine.crud.orgs_locks import CrudOrgsLocks
from dlm_engine.crud.users import CrudUsers


class Api:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_ldap: CrudLdap,
        crud_orgs: CrudOrgs,
        crud_orgs_teams: CrudOrgsTeams,
        crud_users: CrudUsers,
        crud_orgs_packages: CrudOrgsLocks,
        crud_users_credentials: CrudCredentials,
        http: httpx.AsyncClient,
    ):
        self._log = log
        self._router = APIRouter()

        self.router.include_router(
            ApiAuthenticate(
                log=log,
                crud_users=crud_users,
                http=http,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ApiOrgs(
                log=log,
                authorize=authorize,
                crud_orgs=crud_orgs,
                crud_orgs_packages=crud_orgs_packages,
                crud_orgs_teams=crud_orgs_teams,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ApiOrgsLocks(
                log=log,
                authorize=authorize,
                crud_orgs=crud_orgs,
                crud_orgs_locks=crud_orgs_packages,
                crud_orgs_teams=crud_orgs_teams,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ApiOrgsTeams(
                log=log,
                authorize=authorize,
                crud_orgs=crud_orgs,
                crud_orgs_teams=crud_orgs_teams,
                crud_ldap=crud_ldap,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ApiUsers(
                log=log,
                authorize=authorize,
                crud_users=crud_users,
                crud_users_credentials=crud_users_credentials,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ApiUsersCredentials(
                log=log,
                authorize=authorize,
                crud_users=crud_users,
                crud_users_credentials=crud_users_credentials,
            ).router,
            responses={404: {"description": "Not found"}},
        )

    @property
    def router(self):
        return self._router
