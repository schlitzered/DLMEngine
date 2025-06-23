import logging

import httpx
from fastapi import APIRouter

from dlmengine.authorize import Authorize

from dlmengine.controller.api.v1 import ControllerApiV1
from dlmengine.controller.api.v2 import ControllerApiV2

from dlmengine.crud.credentials import CrudCredentials
from dlmengine.crud.ldap import CrudLdap
from dlmengine.crud.locks import CrudLocks
from dlmengine.crud.permissions import CrudPermissions
from dlmengine.crud.users import CrudUsers


class ControllerApi:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_ldap: CrudLdap,
        crud_nodes: CrudLocks,
        crud_permissions: CrudPermissions,
        crud_users: CrudUsers,
        crud_users_credentials: CrudCredentials,
        http: httpx.AsyncClient,
    ):
        self._router = APIRouter()
        self._log = log

        self.router.include_router(
            ControllerApiV2(
                log=log,
                authorize=authorize,
                crud_ldap=crud_ldap,
                crud_nodes=crud_nodes,
                crud_permissions=crud_permissions,
                crud_users=crud_users,
                crud_users_credentials=crud_users_credentials,
                http=http,
            ).router,
            prefix="/v2",
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerApiV1(
                log=log,
                authorize=authorize,
                crud_nodes=crud_nodes,
            ).router,
            prefix="/v1",
            responses={404: {"description": "Not found"}},
        )

    @property
    def router(self):
        return self._router

    @property
    def log(self):
        return self._log
