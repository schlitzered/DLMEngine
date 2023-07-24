import logging

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo
import pymongo.errors

from dlm_engine.crud.common import CrudMongo


from dlm_engine.model.common import DataDelete
from dlm_engine.model.orgs_locks import OrgLockDelete
from dlm_engine.model.orgs_locks import OrgLockGet
from dlm_engine.model.orgs_locks import OrgLockGetMulti
from dlm_engine.model.orgs_locks import OrgLockPost


class CrudOrgsLocks(CrudMongo):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super(CrudOrgsLocks, self).__init__(log=log, coll=coll)

    async def index_create(self) -> None:
        self.log.info(f"creating {self.resource_type} indices")
        await self.coll.create_index(
            [
                ("org", pymongo.ASCENDING),
                ("id", pymongo.ASCENDING),
            ],
            unique=True,
        )
        await self.coll.create_index(
            [
                ("acquired_by", pymongo.ASCENDING),
                ("acquired_since", pymongo.ASCENDING),
            ]
        )
        self.log.info(f"creating {self.resource_type} indices, done")

    async def create(
        self,
        _id: str,
        org_id: str,
        payload: OrgLockPost,
        fields: list,
    ) -> OrgLockGet:
        data = payload.dict()
        data["id"] = _id
        data["org"] = org_id
        result = await self._create(payload=data, fields=fields)
        return OrgLockGet(**result)

    async def delete(
        self,
        _id: str,
        org_id: str,
    ) -> DataDelete:
        query = {"id": _id, "org": org_id}
        await self._delete(query=query)
        return DataDelete()

    async def delete_all_from_org(self, org_id: str):
        query = {
            "org": org_id,
        }
        await self._coll.delete_many(
            filter=query,
        )

    async def delete_mark(
        self,
        _id: str,
        org_id: str,
    ) -> None:
        query = {"id": _id, "org": org_id}
        await self._delete_mark(query=query)

    async def get(
        self,
        _id: str,
        org_id: str,
        fields: list,
    ) -> OrgLockGet:
        query = {"id": _id, "org": org_id}
        result = await self._get(query=query, fields=fields)
        return OrgLockGet(**result)

    async def resource_exists(
        self,
        _id: str,
        org_id: str,
    ) -> ObjectId:
        query = {"id": _id, "org": org_id}
        return await self._resource_exists(query=query)

    async def search(
        self,
        _id: (str, None),
        org_id: (str, None),
        org_filter: (list, None),
        tags: list,
        disabled: bool,
        fields: list,
        sort: str,
        sort_order: str,
        page: int,
        limit: (int, None),
    ) -> OrgLockGetMulti:
        query = {}
        self._filter_re(query, "org", org_id, org_filter)
        self._filter_re(query, "id", _id)
        self._filter_list(query, "tags", tags)
        self._filter_boolean(query, "disabled", disabled)

        result = await self._search(
            query=query,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return OrgLockGetMulti(**result)
