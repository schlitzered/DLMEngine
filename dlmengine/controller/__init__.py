import logging

import httpx
from fastapi import APIRouter

from dlmengine.authorize import Authorize

from dlmengine.controller.api import ControllerApi
from dlmengine.controller.oauth import ControllerOauth

from dlmengine.crud.credentials import CrudCredentials
from dlmengine.crud.ldap import CrudLdap
from dlmengine.crud.locks import CrudLocks
from dlmengine.crud.oauth import CrudOAuth
from dlmengine.crud.permissions import CrudPermissions
from dlmengine.crud.users import CrudUsers


class Controller:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_ldap: CrudLdap,
        crud_locks: CrudLocks,
        crud_oauth: dict[str, CrudOAuth],
        crud_permissions: CrudPermissions,
        crud_users: CrudUsers,
        crud_users_credentials: CrudCredentials,
        http: httpx.AsyncClient,
    ):
        self._log = log
        self._router = APIRouter()

        self.router.include_router(
            ControllerApi(
                log=log,
                authorize=authorize,
                crud_ldap=crud_ldap,
                crud_locks=crud_locks,
                crud_permissions=crud_permissions,
                crud_users=crud_users,
                crud_users_credentials=crud_users_credentials,
                http=http,
            ).router,
            prefix="/api",
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerOauth(
                log=log,
                curd_oauth=crud_oauth,
                crud_users=crud_users,
                http=http,
            ).router,
            prefix="/oauth",
            responses={404: {"description": "Not found"}},
        )

    @property
    def router(self):
        return self._router

    @property
    def log(self):
        return self._log
