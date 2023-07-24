import logging
import sys
import typing
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import pymongo
import pymongo.errors

from dlm_engine.crud.common import CrudMongo

from dlm_engine.model.common import DataDelete
from dlm_engine.model.orgs_teams import OrgTeamGet
from dlm_engine.model.orgs_teams import OrgTeamGetMulti
from dlm_engine.model.orgs_teams import OrgTeamPost
from dlm_engine.model.orgs_teams import OrgTeamPut


class CrudOrgsTeams(CrudMongo):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super(CrudOrgsTeams, self).__init__(log=log, coll=coll)

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
                ("ldap_group", pymongo.ASCENDING),
            ]
        )
        await self.coll.create_index(
            [
                ("users", pymongo.ASCENDING),
            ]
        )
        self.log.info(f"creating {self.resource_type} indices, done")

    async def create(
        self,
        _id: str,
        org_id: str,
        payload: OrgTeamPost,
        fields: list,
    ) -> OrgTeamGet:
        data = payload.dict()
        data["id"] = _id
        data["org"] = org_id
        result = await self._create(payload=data, fields=fields)
        return OrgTeamGet(**result)

    async def delete(
        self,
        _id: str,
        org_id: str,
    ) -> DataDelete:
        query = {"id": _id, "org": org_id}
        await self._delete(query=query)
        return DataDelete()

    async def delete_mark(
        self,
        _id: str,
        org_id: str,
    ) -> None:
        query = {"id": _id, "org": org_id}
        await self._delete_mark(query=query)

    async def delete_all_from_org(self, org_id):
        query = {
            "org": org_id,
        }
        await self._coll.delete_many(
            filter=query,
        )

    async def get(
        self,
        _id: str,
        org_id: str,
        fields: list,
    ) -> OrgTeamGet:
        query = {"id": _id, "org": org_id}
        result = await self._get(query=query, fields=fields)
        return OrgTeamGet(**result)

    async def get_all_orgs_from_user(self, user_id):
        result = set()
        teams = await self.search(
            users=f"^{user_id}$",
            fields=["org"],
            sort="id",
            sort_order="ascending",
            page=0,
            limit=sys.maxsize,
        )
        for team in teams.result:
            result.add(team.org)
        return list(result)

    async def resource_exists(
        self,
        _id: str,
        org_id: str,
    ) -> ObjectId:
        query = {"id": _id, "org": org_id}
        return await self._resource_exists(query=query)

    async def search(
        self,
        _id: typing.Optional[str] = "",
        org_id: str = None,
        org_admin: bool = None,
        ldap_group: typing.Optional[str] = "",
        users: typing.Optional[str] = "",
        fields: typing.Optional[list] = None,
        sort: typing.Optional[str] = None,
        sort_order: typing.Optional[str] = None,
        page: typing.Optional[int] = None,
        limit: typing.Optional[int] = None,
    ) -> OrgTeamGetMulti:
        query = {}
        if org_id:
            self._filter_re(query, "org", f"^{org_id}$")
        self._filter_re(query, "id", _id)
        self._filter_boolean(query, "org_admin", org_admin)
        self._filter_re(query, "ldap_group", ldap_group)
        self._filter_re(query, "users", users)

        result = await self._search(
            query=query,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return OrgTeamGetMulti(**result)

    async def update(
        self,
        _id: str,
        org_id: str,
        payload: OrgTeamPut,
        fields: list,
    ) -> OrgTeamGet:
        query = {"id": _id, "org": org_id}
        data = payload.dict()

        result = await self._update(query=query, fields=fields, payload=data)
        return OrgTeamGet(**result)
