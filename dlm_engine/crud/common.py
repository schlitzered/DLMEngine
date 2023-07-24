import logging
import typing

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo
import pymongo.errors

from dlm_engine.crud.mixins import FilterMixIn
from dlm_engine.crud.mixins import Format
from dlm_engine.crud.mixins import PaginationSkipMixIn
from dlm_engine.crud.mixins import ProjectionMixIn
from dlm_engine.crud.mixins import SortMixIn

from dlm_engine.errors import DuplicateResource
from dlm_engine.errors import ResourceNotFound
from dlm_engine.errors import BackendError


class Crud:
    def __init__(self, log: logging.Logger):
        self._log = log

    @property
    def log(self):
        return self._log


class CrudMongo(
    Crud, FilterMixIn, Format, PaginationSkipMixIn, ProjectionMixIn, SortMixIn
):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super().__init__(log)
        self._resource_type = coll.name
        self._coll = coll

    @property
    def coll(self):
        return self._coll

    @property
    def resource_type(self):
        return self._resource_type

    async def _create(
        self,
        payload: dict,
        fields: list = None,
    ) -> dict:
        payload["deleting"] = False
        try:
            _id = await self._coll.insert_one(payload)
            return await self._get_by_obj_id(_id=_id.inserted_id, fields=fields)
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateResource
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError()

    async def _delete(self, query: dict) -> dict:
        try:
            result = await self._coll.delete_one(filter=query)
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError()
        if result.deleted_count == 0:
            raise ResourceNotFound
        return {}

    async def _delete_mark(self, query: dict) -> None:
        update = {"$set": {"deleting": True}}
        try:
            await self._coll.update_one(
                filter=query,
                update=update,
            )
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError

    async def _get(self, query: dict, fields: list) -> dict:
        # todo: after migration, adjust all documents to have this field
        # payload["deleting"] = False
        try:
            result = await self._coll.find_one(
                filter=query, projection=self._projection(fields)
            )
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError
        if result is None:
            raise ResourceNotFound(
                details=f"Resource {self.resource_type} {query} not found"
            )
        return self._format(result)

    async def _get_by_obj_id(self, _id, fields: list) -> dict:
        # todo: after migration, adjust all documents to have this field
        # query["deleting"] = False
        query = {"_id": _id}
        return await self._get(query=query, fields=fields)

    async def _resource_exists(self, query: dict) -> ObjectId:
        result = await self._get(query=query, fields=["id"])
        return result["id"]

    async def _search(
        self,
        query: dict,
        fields: typing.Optional[list] = None,
        sort: typing.Optional[str] = None,
        sort_order: typing.Optional[str] = None,
        page: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
    ) -> dict:
        # todo: after migration, adjust all documents to have this field
        # query["deleting"] = False
        try:
            count = await self._coll.count_documents(filter=query)
            cursor = self._coll.find(filter=query, projection=self._projection(fields))
            cursor.sort(self._sort(sort=sort, sort_order=sort_order))
            cursor.skip(self._pagination_skip(page, limit))
            cursor.limit(limit)
            result = list()
            for item in await cursor.to_list(limit):
                result.append(item)
            return self._format_multi(result, count=count)
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError

    async def _update(self, query: dict, payload: dict, fields: list) -> dict:
        # todo: after migration, adjust all documents to have this field
        # query["deleting"] = False
        update = {"$set": {}}
        for k, v in payload.items():
            if v is None:
                continue
            update["$set"][k] = v
        try:
            result = await self._coll.find_one_and_update(
                filter=query,
                update=update,
                projection=self._projection(fields=fields),
                return_document=pymongo.ReturnDocument.AFTER,
            )
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError
        if result is None:
            raise ResourceNotFound
        return self._format(result)
