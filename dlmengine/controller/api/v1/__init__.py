import logging

from fastapi import APIRouter

from dlmengine.authorize import Authorize

from dlmengine.controller.api.v1.locks import ControllerApiV1Locks

from dlmengine.crud.locks import CrudLocks


class ControllerApiV1:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_locks: CrudLocks,
    ):
        self._router = APIRouter()
        self._log = log

        self.router.include_router(
            ControllerApiV1Locks(
                log=log,
                authorize=authorize,
                crud_locks=crud_locks,
            ).router,
            responses={404: {"description": "Not found"}},
        )

    @property
    def router(self):
        return self._router
