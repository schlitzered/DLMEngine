import logging

from fastapi import Request

from dlm_engine.crud.users import CrudUsers
from dlm_engine.crud.orgs_teams import CrudOrgsTeams

from dlm_engine.errors import AdminError
from dlm_engine.errors import OrgAdminError
from dlm_engine.errors import OrgMemberError
from dlm_engine.errors import PermError
from dlm_engine.errors import SessionCredentialError

from dlm_engine.model.users import UserGet


class Authorize:
    def __init__(
        self,
        log: logging.Logger,
        crud_orgs_teams: CrudOrgsTeams,
        crud_users: CrudUsers,
    ):
        self._crud_orgs_teams = crud_orgs_teams
        self._crud_users = crud_users
        self._log = log

    @property
    def crud_orgs_teams(self) -> CrudOrgsTeams:
        return self._crud_orgs_teams

    @property
    def crud_users(self) -> CrudUsers:
        return self._crud_users

    @property
    def log(self):
        return self._log

    async def get_user(self, request: Request):
        user = self.get_user_from_session(request=request)
        if not user:
            user = await self.get_user_from_credentials(request=request)
        if not user:
            raise SessionCredentialError
        user = await self.crud_users.get(_id=user, fields=["id", "admin"])
        return user

    async def get_user_groups(self, user):
        user_groups = await self.crud_orgs_teams.search(users=f"^{user}!")
        result = list()
        for group in user_groups.result:
            result.append(group.id)
        return result

    async def get_user_from_credentials(self, request: Request):
        pass

    def get_user_from_session(self, request: Request):
        self.log.debug("trying to get user from session")
        user = request.session.get("username", None)
        self.log.debug(f"received user {user} from session")
        return user

    async def require_admin(self, request, user=None) -> UserGet:
        if not user:
            user = await self.get_user(request=request)
        if not user.admin:
            raise AdminError
        return user

    async def require_org_admin(self, request, org_id, user=None) -> UserGet:
        if not user:
            user = await self.get_user(request)
        try:
            return await self.require_admin(request=request, user=user)
        except AdminError:
            pass
        teams = await self.crud_orgs_teams.search(
            org_id=org_id,
            org_admin=True,
            users=f"^{user.id}$",
            sort="id",
            sort_order="ascending",
            page=0,
            limit=10,
            fields=["id"],
        )
        if not teams.result:
            raise OrgAdminError
        return user

    async def require_org_member(self, request, org_id, user=None) -> UserGet:
        if not user:
            user = await self.get_user(request)
        try:
            return await self.require_admin(request=request, user=user)
        except AdminError:
            pass
        permissions = await self.crud_orgs_teams.search(
            org_id=org_id,
            users=f"^{user.id}$",
            sort="id",
            sort_order="ascending",
            page=0,
            limit=10,
            fields=["id"],
        )
        if not permissions.result:
            raise OrgMemberError
        return user

    async def require_user(self, request) -> UserGet:
        user = await self.get_user(request)
        return user
