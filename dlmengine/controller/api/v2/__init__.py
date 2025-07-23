import logging

import httpx
from fastapi import APIRouter

from dlmengine.authorize import Authorize

from dlmengine.controller.api.v2.authenticate import ControllerApiV2Authenticate
from dlmengine.controller.api.v2.locks import ControllerApiV2Locks
from dlmengine.controller.api.v2.permissions import ControllerApiV2Permissions
from dlmengine.controller.api.v2.users import ControllerApiV2Users
from dlmengine.controller.api.v2.users_credentials import (
    ControllerApiV2UsersCredentials,
)

from dlmengine.crud.credentials import CrudCredentials
from dlmengine.crud.ldap import CrudLdap
from dlmengine.crud.locks import CrudLocks
from dlmengine.crud.permissions import CrudPermissions
from dlmengine.crud.users import CrudUsers


class ControllerApiV2:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_ldap: CrudLdap,
        crud_locks: CrudLocks,
        crud_permissions: CrudPermissions,
        crud_users: CrudUsers,
        crud_users_credentials: CrudCredentials,
        http: httpx.AsyncClient,
    ):
        self._router = APIRouter()
        self._log = log

        self.router.include_router(
            ControllerApiV2Authenticate(
                log=log,
                authorize=authorize,
                crud_users=crud_users,
                http=http,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerApiV2Locks(
                log=log,
                authorize=authorize,
                crud_locks=crud_locks,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerApiV2Permissions(
                log=log,
                authorize=authorize,
                crud_permissions=crud_permissions,
                crud_ldap=crud_ldap,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerApiV2Users(
                log=log,
                authorize=authorize,
                crud_permissions=crud_permissions,
                crud_users=crud_users,
                crud_users_credentials=crud_users_credentials,
            ).router,
            responses={404: {"description": "Not found"}},
        )

        self.router.include_router(
            ControllerApiV2UsersCredentials(
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
