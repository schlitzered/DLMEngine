import logging
import typing
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo
import pymongo.errors

from dlm_engine.crud.common import CrudMongo

from dlm_engine.model.common import DataDelete
from dlm_engine.model.orgs import OrgGet
from dlm_engine.model.orgs import OrgGetMulti
from dlm_engine.model.orgs import OrgPost
from dlm_engine.model.orgs import OrgPut


class CrudOrgs(CrudMongo):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super(CrudOrgs, self).__init__(log=log, coll=coll)

    async def index_create(self) -> None:
        self.log.info(f"creating {self.resource_type} indices")
        await self.coll.create_index([("id", pymongo.ASCENDING)], unique=True)
        self.log.info(f"creating {self.resource_type} indices, done")

    async def create(
        self,
        _id: str,
        payload: OrgPost,
        fields: list,
    ) -> OrgGet:
        data = payload.dict()
        data["id"] = _id
        result = await self._create(payload=data, fields=fields)
        return OrgGet(**result)

    async def delete(self, _id: str) -> DataDelete:
        query = {"id": _id}
        await self._delete(query=query)
        return DataDelete()

    async def delete_mark(self, _id: str) -> None:
        query = {"id": _id}
        await self._delete_mark(query=query)

    async def get(self, _id: str, fields: list) -> OrgGet:
        query = {"id": _id}
        result = await self._get(query=query, fields=fields)
        return OrgGet(**result)

    async def resource_exists(self, _id: str) -> ObjectId:
        query = {"id": _id}
        return await self._resource_exists(query=query)

    async def search(
        self,
        _id: typing.Optional[str] = "",
        _id_filter: typing.Optional[list] = [],
        fields: typing.Optional[list] = None,
        sort: typing.Optional[str] = None,
        sort_order: typing.Optional[str] = None,
        page: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
    ) -> OrgGetMulti:
        query = {}
        self._filter_re(query, "id", _id, _id_filter)
        self.log.info(query)

        result = await self._search(
            query=query,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return OrgGetMulti(**result)

    async def update(self, _id: str, payload: OrgPut, fields: list) -> OrgGet:
        query = {"id": _id}
        data = payload.dict()

        result = await self._update(query=query, fields=fields, payload=data)
        return OrgGet(**result)
