__author__ = 'schlitzer'

import datetime

import pymongo
import pymongo.errors

from dlm_engine.models.mixins import Format, FilterMixIn, PaginationSkipMixIn, ProjectionMixIn, SortMixIn
from dlm_engine.models.mixins import pagination_from_schema
from dlm_engine.models.mixins import projection_from_schema
from dlm_engine.models.mixins import sort_from_schema
from dlm_engine.errors import MongoConnError, ResourceNotFound, DuplicateResource
from dlm_engine.schemes import schemes


class Locks(Format, FilterMixIn, PaginationSkipMixIn, ProjectionMixIn, SortMixIn):
    def __init__(self, coll):
        super().__init__()
        self.pagination_steps = pagination_from_schema(
            schema=schemes, path='/locks/_search'
        )
        self.pagination_limit = self.pagination_steps[-1]
        self.projection_fields = projection_from_schema(
            schema=schemes, path='/locks/_search'
        )
        self.sort_fields = sort_from_schema(
            schema=schemes, path='/locks/_search'
        )
        self._coll = coll

    async def create(self, _id, payload):
        payload['id'] = _id
        payload['acquired_since'] = datetime.datetime.utcnow()
        try:
            await self._coll.insert_one(payload)
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateResource(_id)
        except pymongo.errors.ConnectionFailure as err:
            raise MongoConnError(err)
        return await self.get(_id)

    async def delete(self, _id, payload):
        try:
            if 'force' in payload:
                result = await self._coll.delete_one(filter={
                    'id': _id,

                })
            else:
                query = {
                    'id': _id,
                    'acquired_by': payload['acquired_by'],
                }
                if 'secret' in payload:
                    query['secret'] = payload['secret']
                else:
                    query['secret'] = None
                result = await self._coll.delete_one(filter=query)

        except pymongo.errors.ConnectionFailure as err:
            raise MongoConnError(err)
        if result.deleted_count is 0:
            raise ResourceNotFound(_id)
        return

    async def get(self, _id, fields=None):
        try:
            result = await self._coll.find_one(
                filter={
                    'id': _id,
                },
                projection=self._projection(fields)
            )
        except pymongo.errors.ConnectionFailure as err:
            raise MongoConnError(err)
        if result is None:
            raise ResourceNotFound(_id)
        if 'acquired_since' in result:
            result['acquired_since'] = result['acquired_since'].replace(tzinfo=datetime.timezone.utc).isoformat()
        return self._format(result)

    async def search(
            self, locks=None, acquired_by=None,
            fields=None, sort=None, page=None, limit=None):
        query = {}
        self._filter_re(query, 'id', locks)
        self._filter_re(query, 'acquired_by', acquired_by)
        try:
            cursor = self._coll.find(
                filter=query,
                projection=self._projection(fields)
            )
            cursor.sort(self._sort(sort))
            cursor.skip(self._pagination_skip(page, limit))
            cursor.limit(self._pagination_limit(limit))
            result = list()
            for item in await cursor.to_list(self._pagination_limit(limit)):
                if 'acquired_since' in item:
                    item['acquired_since'] = item['acquired_since'].replace(tzinfo=datetime.timezone.utc).isoformat()
                result.append(self._format(item))
            return self._format(result, multi=True)
        except pymongo.errors.ConnectionFailure as err:
            raise MongoConnError(err)
