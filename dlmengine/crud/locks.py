import datetime
import logging
import typing

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo
import pymongo.errors

from dlmengine.crud.common import CrudMongo


from dlmengine.model.v2.common import ModelV2DataDelete
from dlmengine.model.v2.common import sort_order_literal
from dlmengine.model.v2.locks import ModelV2LockGet
from dlmengine.model.v2.locks import ModelV2LockGetMulti
from dlmengine.model.v2.locks import ModelV2LockPost


class CrudLocks(CrudMongo):
    def __init__(
        self,
        log: logging.Logger,
        coll: AsyncIOMotorCollection,
    ):
        super(CrudLocks, self).__init__(log=log, coll=coll)

    async def index_create(self) -> None:
        self.log.info(f"creating {self.resource_type} indices")
        await self.coll.create_index([("id", pymongo.ASCENDING)], unique=True)
        await self.coll.create_index([("deleting", pymongo.ASCENDING)])
        self.log.info(f"creating {self.resource_type} indices, done")

    async def create(
        self, _id: str, payload: ModelV2LockPost, fields: list
    ) -> ModelV2LockGet:
        data = payload.model_dump()
        data["id"] = _id
        data["acquired_since"] = datetime.datetime.utcnow()

        result = await self._create(fields=fields, payload=data)
        return ModelV2LockGet(**result)

    async def delete(
        self,
        _id: str,
    ) -> ModelV2DataDelete:
        query = {"id": _id}
        await self._delete(query=query)
        return ModelV2DataDelete()

    async def delete_mark(
        self,
        _id: str,
    ) -> None:
        query = {"id": _id}
        await self._delete_mark(query=query)

    async def get(
        self,
        _id: str,
        fields: list,
    ) -> ModelV2LockGet:
        query = {"id": _id}
        result = await self._get(query=query, fields=fields)
        return ModelV2LockGet(**result)

    async def resource_exists(
        self,
        _id: str,
    ) -> ObjectId:
        query = {"id": _id}
        return await self._resource_exists(query=query)

    async def search(
        self,
        _id: typing.Optional[str] = None,
        fields: typing.Optional[list] = None,
        sort: typing.Optional[str] = None,
        sort_order: typing.Optional[sort_order_literal] = None,
        page: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
        query: typing.Optional[dict] = None,
    ) -> ModelV2LockGetMulti:
        if not query:
            query = {}
        self._filter_re(query, "id", _id)
        result = await self._search(
            query=query,
            fields=fields,
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return ModelV2LockGetMulti(**result)
