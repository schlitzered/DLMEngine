import logging


from fastapi import APIRouter
from fastapi import Request
from fastapi_versionizer import api_version

import httpx

from dlm_engine.crud.users import CrudUsers

from dlm_engine.errors import AuthenticationError

from dlm_engine.model.common import DataDelete
from dlm_engine.model.authenticate import AuthenticateGetUser
from dlm_engine.model.authenticate import AuthenticatePost


class ApiAuthenticate:
    def __init__(
        self,
        log: logging.Logger,
        crud_users: CrudUsers,
        http: httpx.AsyncClient,
    ):
        self._crud_users = crud_users
        self._http = http
        self._log = log
        self._router = APIRouter(
            prefix="/authenticate",
            tags=["authenticate"],
        )

        self.router.add_api_route(
            "", self.get, response_model=AuthenticateGetUser, methods=["GET"]
        )
        self.router.add_api_route(
            "",
            self.create,
            response_model=AuthenticateGetUser,
            methods=["POST"],
            status_code=201,
        )
        self.router.add_api_route(
            "", self.delete, response_model=DataDelete, methods=["DELETE"]
        )

    @property
    def crud_users(self):
        return self._crud_users

    @property
    def http(self):
        return self._http

    @property
    def log(self):
        return self._log

    @property
    def router(self):
        return self._router

    @api_version(2)
    async def get(self, request: Request):
        user = request.session.get("username", None)
        if not user:
            raise AuthenticationError
        return {"user": user}

    @api_version(2)
    async def create(
        self,
        data: AuthenticatePost,
        request: Request,
    ):
        user = await self.crud_users.check_credentials(credentials=data)
        request.session["username"] = user
        return {"user": user}

    @api_version(2)
    async def delete(self, request: Request):
        request.session.clear()
        return {}
