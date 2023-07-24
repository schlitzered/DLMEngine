import datetime
import logging
import random
import string
import uuid

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.hash import pbkdf2_sha512
import pymongo

from dlm_engine.crud.common import CrudMongo

from dlm_engine.errors import CredentialError
from dlm_engine.errors import ResourceNotFound

from dlm_engine.model.common import DataDelete
from dlm_engine.model.credentials import CredentialGet
from dlm_engine.model.credentials import CredentialGetMulti
from dlm_engine.model.credentials import CredentialPost
from dlm_engine.model.credentials import CredentialPostResult
from dlm_engine.model.credentials import CredentialPut


class CrudCredentials(CrudMongo):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super(CrudCredentials, self).__init__(log=log, coll=coll)

    @staticmethod
    def _create_secret(token) -> str:
        return pbkdf2_sha512.encrypt(str(token), rounds=10, salt_size=32)

    async def index_create(self) -> None:
        self.log.info(f"creating {self.resource_type} indices")
        await self.coll.create_index(
            [("id", pymongo.ASCENDING), ("owner", pymongo.ASCENDING)], unique=True
        )
        self.log.info(f"creating {self.resource_type} indices, done")

    async def check_credential(self, request: Request):
        x_secret = request.headers.get("x-secret")
        x_secret_id = request.headers.get("x-secret-id")

        query = {"id": x_secret_id}

        result = await self._get(query=query, fields=["secret"])

        if not pbkdf2_sha512.verify(x_secret, result["secret"]):
            raise CredentialError

        return {"user": result["owner"]}

    async def create(
        self,
        owner: str,
        payload: CredentialPost,
    ) -> CredentialPostResult:
        data = payload.dict()
        _id = uuid.uuid4()
        secret = "".join(
            random.SystemRandom().choice(string.ascii_letters + string.digits + "_-.")
            for _ in range(128)
        )
        created = datetime.datetime.utcnow()
        data["id"] = str(_id)
        data["secret"] = self._create_secret(str(secret))
        data["created"] = created
        data["owner"] = owner
        await self._create(payload=data, fields=["id"])
        result = {
            "id": str(_id),
            "created": str(created),
            "description": payload.description,
            "secret": str(secret),
        }
        return CredentialPostResult(**result)

    async def delete(self, _id: str, owner: str) -> DataDelete:
        query = {"id": _id, "owner": owner}
        await self._delete(query=query)
        return DataDelete()

    async def delete_all_from_owner(self, owner: str) -> DataDelete:
        query = {"owner": owner}
        try:
            await self._delete(query=query)
        except ResourceNotFound:
            pass
        return DataDelete()

    async def get(self, _id: str, owner: str, fields: list) -> CredentialGet:
        query = {"id": str(_id), "owner": owner}
        result = await self._get(query=query, fields=fields)
        if "created" in result:
            result["created"] = str(result["created"])
        self.log.info(result)
        return CredentialGet(**result)

    async def search(
        self,
        owner: str,
        fields: list,
        sort: str,
        sort_order: str,
        page: int,
        limit: int,
    ) -> CredentialGetMulti:
        query = {"owner": owner}

        result = await self._search(
            query=query,
            fields=fields,
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        for item in result["result"]:
            if "created" in item:
                item["created"] = str(item["created"])
        return CredentialGetMulti(**result)

    async def update(
        self, _id: str, owner: str, payload: CredentialPut, fields: list
    ) -> CredentialGet:
        query = {"id": _id, "owner": owner}
        data = payload.dict()
        result = await self._update(query=query, fields=fields, payload=data)
        if "created" in result:
            result["created"] = str(result["created"])
        return CredentialGet(**result)
