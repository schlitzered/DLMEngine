__author__ = 'schlitzer'

import datetime

import pymongo
import pymongo.errors

from dlm_engine.models.mixins import Format, FilterMixIn, PaginationSkipMixIn, ProjectionMixIn, SortMixIn
from dlm_engine.errors import MongoConnError, PermError, ResourceNotFound, DuplicateResource


class Locks(Format, FilterMixIn, PaginationSkipMixIn, ProjectionMixIn, SortMixIn):
    def __init__(self, coll):
        super().__init__()
        self.projection_fields = {
            '_id': 1,
            'acquired_by': 1,
            'acquired_since': 1
        }
        self.sort_fields = [
            ('_id', pymongo.ASCENDING),
        ]
        self._coll = coll

    async def create(self, _id, payload):
        payload['_id'] = _id
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
                    '_id': _id,

                })
            else:
                query = {
                    '_id': _id,
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
                    '_id': _id,
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
        self._filter_re(query, '_id', locks)
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
