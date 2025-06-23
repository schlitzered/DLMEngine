import logging
from typing import Set

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request

from dlmengine.authorize import Authorize

from dlmengine.crud.locks import CrudLocks

from dlmengine.model.v2.common import ModelV2DataDelete
from dlmengine.model.v2.common import sort_order_literal
from dlmengine.model.v2.locks import filter_list
from dlmengine.model.v2.locks import filter_literal
from dlmengine.model.v2.locks import sort_literal
from dlmengine.model.v2.locks import ModelV2LockGet
from dlmengine.model.v2.locks import ModelV2LockGetMulti
from dlmengine.model.v2.locks import ModelV2LockPost


class ControllerApiV2Locks:

    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_locks: CrudLocks,
    ):
        self._authorize = authorize
        self._crud_locks = crud_locks
        self._log = log
        self._router = APIRouter(
            prefix="/locks",
            tags=["locks"],
        )

        self.router.add_api_route(
            "",
            self.search,
            response_model=ModelV2LockGetMulti,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.create,
            response_model=ModelV2LockGet,
            response_model_exclude_unset=True,
            methods=["POST"],
            status_code=201,
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.delete,
            response_model=ModelV2DataDelete,
            response_model_exclude_unset=True,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.get,
            response_model=ModelV2LockGet,
            response_model_exclude_unset=True,
            methods=["GET"],
        )

    @property
    def authorize(self):
        return self._authorize

    @property
    def crud_locks(self):
        return self._crud_locks

    @property
    def log(self):
        return self._log

    @property
    def router(self):
        return self._router

    async def create(
        self,
        data: ModelV2LockPost,
        lock_id: str,
        request: Request,
        fields: Set[filter_literal] = Query(default=filter_list),
    ):
        await self.authorize.require_permission(request=request, permission="LOCK:POST")

        return await self.crud_locks.create(
            _id=lock_id, payload=data, fields=list(fields)
        )

    async def delete(self, request: Request, lock_id: str):
        await self.authorize.require_permission(
            request=request, permission="LOCK:DELETE"
        )
        await self.crud_locks.delete_mark(_id=lock_id)
        return await self.crud_locks.delete(_id=lock_id)

    async def get(
        self,
        lock_id: str,
        request: Request,
        fields: Set[filter_literal] = Query(default=filter_list),
    ):
        user = await self.authorize.require_user(request=request)
        return await self.crud_locks.get(_id=lock_id, fields=list(fields))

    async def search(
        self,
        request: Request,
        lock_id: str = Query(description="filter: regular_expressions", default=None),
        fields: Set[filter_literal] = Query(default=filter_list),
        sort: sort_literal = Query(default="id"),
        sort_order: sort_order_literal = Query(default="ascending"),
        page: int = Query(default=0, ge=0, description="pagination index"),
        limit: int = Query(
            default=10,
            ge=10,
            le=1000,
            description="pagination limit, min value 10, max value 1000",
        ),
    ):
        user = await self.authorize.require_user(request=request)

        return await self.crud_locks.search(
            _id=lock_id,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
