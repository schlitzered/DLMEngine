__author__ = 'schlitzer'
import jsonschema
import jsonschema.exceptions

from aiohttp.web import json_response
from dlm_engine.schemes import LOCKS_CREATE, LOCKS_DELETE


class Locks:
    def __init__(self, aa, locks):
        self._aa = aa
        self._locks = locks

    @property
    def aa(self):
        return self._aa

    @property
    def locks(self):
        return self._locks

    async def delete(self, request):
        await self.aa.require(request, 'LOCK:ACQUIRE_RELEASE')
        lock = request.match_info['lock']
        payload = await request.json()
        jsonschema.validate(payload, LOCKS_DELETE, format_checker=jsonschema.draft4_format_checker)
        payload = payload.get('data')
        if 'force' in payload:
            await self.aa.require(request, 'LOCK:DELETE')
        else:
            payload.pop('force', None)
        return json_response(await self.locks.delete(lock, payload))

    async def get(self, request):
        await self.aa.require(request, 'LOCK:GET')
        lock = request.match_info['lock']
        fields = request.query.get('fields', None)
        return json_response(await self.locks.get(lock, fields))

    async def post(self, request):
        await self.aa.require(request, 'LOCK:ACQUIRE_RELEASE')
        lock = request.match_info['lock']
        payload = await request.json()
        jsonschema.validate(payload, LOCKS_CREATE, format_checker=jsonschema.draft4_format_checker)
        payload = payload.get('data')
        result = await self.locks.create(lock, payload)
        return json_response(result, status=201)

    async def search(self, request):
        await self.aa.require(request, 'LOCK:GET')
        result = await self.locks.search(
            locks=request.query.get('locks', None),
            acquired_by=request.query.get('acquired_by', None),
            fields=request.query.get('fields', None),
            sort=request.query.get('sort', None),
            page=request.query.get('page', None),
            limit=request.query.get('limit', None)
        )
        return json_response(result)
