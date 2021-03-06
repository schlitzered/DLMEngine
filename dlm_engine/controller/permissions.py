__author__ = 'schlitzer'
import jsonschema
import jsonschema.exceptions

from aiohttp.web import json_response
from dlm_engine.schemes import PERMISSIONS_CREATE, PERMISSIONS_UPDATE
from dlm_engine.errors import ResourceNotFound


class Permissions:
    def __init__(self, aa, permissions, users):
        self._aa = aa
        self._permissions = permissions
        self._users = users

    @property
    def aa(self):
        return self._aa

    @property
    def permissions(self):
        return self._permissions

    @property
    def users(self):
        return self._users

    async def delete(self, request):
        await self.aa.require_admin(request)
        perm = request.match_info['perm']
        await self.permissions.delete_mark(perm)
        return json_response(await self.permissions.delete(perm))

    async def get(self, request):
        await self.aa.require_admin(request)
        perm = request.match_info['perm']
        fields = request.query.get('fields', None)
        return json_response(await self.permissions.get(perm, fields))

    async def post(self, request):
        await self.aa.require_admin(request)
        perm = request.match_info['perm']
        payload = await request.json()
        jsonschema.validate(payload, PERMISSIONS_CREATE, format_checker=jsonschema.draft4_format_checker)
        payload = payload.get('data')
        for user in payload['users']:
            if not await self.users.resource_exists(user):
                raise ResourceNotFound("User: {0}".format(user))
        result = await self.permissions.create(perm, payload)
        return json_response(result, status=201)

    async def put(self, request):
        await self.aa.require_admin(request)
        perm = request.match_info['perm']
        payload = await request.json()
        jsonschema.validate(payload, PERMISSIONS_UPDATE, format_checker=jsonschema.draft4_format_checker)
        payload = payload.get('data')
        if 'users' in payload:
            for user in payload['users']:
                if not await self.users.resource_exists(user):
                    raise ResourceNotFound("User: {0}".format(user))
        result = await self.permissions.update(perm, payload)
        return json_response(result, status=201)

    async def search(self, request):
        await self.aa.require_admin(request)
        result = await self.permissions.search(
            permissions=request.query.get('permissions', None),
            users=request.query.get('users', None),
            fields=request.query.get('fields', None),
            sort=request.query.get('sort', None),
            page=request.query.get('page', None),
            limit=request.query.get('limit', None)
        )
        return json_response(result)
