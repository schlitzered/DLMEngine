import logging

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from passlib.hash import pbkdf2_sha512
import pymongo
import pymongo.errors

from dlm_engine.crud.common import CrudMongo

from dlm_engine.errors import AuthenticationError
from dlm_engine.errors import BackendError

from dlm_engine.model.common import DataDelete
from dlm_engine.model.authenticate import AuthenticatePost
from dlm_engine.model.users import UserGet
from dlm_engine.model.users import UserGetMulti
from dlm_engine.model.users import UserPost
from dlm_engine.model.users import UserPut


class CrudUsers(CrudMongo):
    def __init__(self, log: logging.Logger, coll: AsyncIOMotorCollection):
        super(CrudUsers, self).__init__(log=log, coll=coll)

    async def index_create(self) -> None:
        self.log.info(f"creating {self.resource_type} indices")
        await self.coll.create_index([("id", pymongo.ASCENDING)], unique=True)
        self.log.info(f"creating {self.resource_type} indices, done")

    @staticmethod
    def _password(password) -> str:
        return pbkdf2_sha512.encrypt(password, rounds=100000, salt_size=32)

    async def check_credentials(self, credentials: AuthenticatePost) -> str:
        user = credentials.user
        password = credentials.password
        try:
            result = await self._coll.find_one(
                filter={"id": user, "deleting": False, "backend": "internal"},
                projection={"password": 1},
            )
            if not result:
                raise AuthenticationError
            if not pbkdf2_sha512.verify(password, result["password"]):
                raise AuthenticationError
            return user
        except pymongo.errors.ConnectionFailure as err:
            self.log.error(f"backend error: {err}")
            raise BackendError()

    async def create(
        self,
        _id: str,
        payload: UserPost,
        fields: list,
    ) -> UserGet:
        data = payload.dict()
        data["id"] = _id
        data["password"] = self._password(payload.password)
        data["backend"] = "internal"
        data["backend_ref"] = "internal"
        result = await self._create(payload=data, fields=fields)
        return UserGet(**result)

    async def create_external(
        self, _id: str, payload: UserPut, fields: list, backend: str, backend_ref: str
    ) -> UserGet:
        data = payload.dict()
        data["id"] = _id
        data["backend"] = backend
        data["backend_ref"] = backend_ref
        result = await self._create(payload=data, fields=fields)
        return UserGet(**result)

    async def delete(self, _id: str) -> DataDelete:
        query = {"id": _id}
        await self._delete(query=query)
        return DataDelete()

    async def delete_mark(self, _id: str) -> None:
        query = {"id": _id}
        await self._delete_mark(query=query)

    async def get(self, _id: str, fields: list) -> UserGet:
        query = {"id": _id}
        result = await self._get(query=query, fields=fields)
        return UserGet(**result)

    async def resource_exists(self, _id: str) -> ObjectId:
        query = {"id": _id}
        return await self._resource_exists(query=query)

    async def search(
        self, _id: str, fields: list, sort: str, sort_order: str, page: int, limit: int
    ) -> UserGetMulti:
        query = {}
        self._filter_re(query, "id", _id)

        result = await self._search(
            query=query,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        return UserGetMulti(**result)

    async def update(self, _id: str, payload: UserPut, fields: list) -> UserGet:
        query = {"id": _id}
        data = payload.dict()
        if data["password"] is not None:
            user_orig = await self.get(_id=_id, fields=["backend"])
            if user_orig.backend == "internal":
                data["password"] = self._password(data["password"])
            else:
                data["passwort"] = None

        result = await self._update(query=query, fields=fields, payload=data)
        return UserGet(**result)
