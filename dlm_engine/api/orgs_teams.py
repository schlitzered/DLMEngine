import logging
from typing import Set
from typing import Union

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi_versionizer import api_version

from dlm_engine.authorize import Authorize

from dlm_engine.crud.orgs import CrudOrgs
from dlm_engine.crud.orgs_teams import CrudOrgsTeams
from dlm_engine.crud.ldap import CrudLdap

from dlm_engine.model.common import DataDelete
from dlm_engine.model.orgs import OrgId
from dlm_engine.model.orgs_teams import filter_list
from dlm_engine.model.orgs_teams import filter_literal
from dlm_engine.model.orgs_teams import sort_literal
from dlm_engine.model.orgs_teams import sort_order_literal
from dlm_engine.model.orgs_teams import OrgTeamGet
from dlm_engine.model.orgs_teams import OrgTeamGetMulti
from dlm_engine.model.orgs_teams import OrgTeamPost
from dlm_engine.model.orgs_teams import OrgTeamPut


class ApiOrgsTeams:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_orgs: CrudOrgs,
        crud_orgs_teams: CrudOrgsTeams,
        crud_ldap: CrudLdap,
    ):
        self._authorize = authorize
        self._crud_orgs = crud_orgs
        self._crud_orgs_teams = crud_orgs_teams
        self._crud_ldap = crud_ldap
        self._log = log
        self._router = APIRouter(
            prefix="/orgs/{org_id}/teams",
            tags=["orgs_teams"],
        )

        self.router.add_api_route(
            "",
            self.search,
            response_model=OrgTeamGetMulti,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{team_id}",
            self.create,
            response_model=OrgTeamGet,
            response_model_exclude_unset=True,
            methods=["POST"],
            status_code=201,
        )
        self.router.add_api_route(
            "/{team_id}",
            self.delete,
            response_model=DataDelete,
            response_model_exclude_unset=True,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/{team_id}",
            self.get,
            response_model=OrgTeamGet,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{team_id}",
            self.update,
            response_model=OrgTeamGet,
            response_model_exclude_unset=True,
            methods=["PUT"],
        )

    @property
    def authorize(self):
        return self._authorize

    @property
    def crud_orgs(self):
        return self._crud_orgs

    @property
    def crud_orgs_teams(self):
        return self._crud_orgs_teams

    @property
    def crud_ldap(self):
        return self._crud_ldap

    @property
    def log(self):
        return self._log

    @property
    def router(self):
        return self._router

    @api_version(2)
    async def create(
        self,
        request: Request,
        data: OrgTeamPost,
        team_id: str,
        org_id: OrgId,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        if data.ldap_group:
            data.users = await self.crud_ldap.get_logins_from_group(
                group=data.ldap_group
            )
        return await self.crud_orgs_teams.create(
            _id=team_id,
            org_id=org_id,
            payload=data,
            fields=list(fields),
        )

    @api_version(2)
    async def delete(
        self,
        request: Request,
        team_id: str,
        org_id: OrgId,
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        await self.crud_orgs_teams.delete_mark(
            _id=team_id,
            org_id=org_id,
        )
        return await self.crud_orgs_teams.delete(
            _id=team_id,
            org_id=org_id,
        )

    @api_version(2)
    async def get(
        self,
        team_id: str,
        org_id: OrgId,
        request: Request,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        return await self.crud_orgs_teams.get(
            _id=team_id, org_id=org_id, fields=list(fields)
        )

    @api_version(2)
    async def search(
        self,
        request: Request,
        org_id: OrgId,
        team_id: str = Query(description="filter: regular_expressions", default=None),
        org_admin: bool = Query(description="filter: boolean", default=None),
        ldap_group: str = Query(
            description="filter: regular_expressions", default=None
        ),
        users: str = Query(description="filter: regular_expressions", default=None),
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
        sort: Union[sort_literal, None] = Query(default="id"),
        sort_order: Union[sort_order_literal, None] = Query(default="ascending"),
        page: int = Query(default=0, ge=0, description="pagination index"),
        limit: int = Query(
            default=10,
            ge=10,
            le=1000,
            description="pagination limit, min value 10, max value 1000",
        ),
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        return await self.crud_orgs_teams.search(
            _id=team_id,
            org_id=org_id,
            org_admin=org_admin,
            ldap_group=ldap_group,
            users=users,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

    @api_version(2)
    async def update(
        self,
        data: OrgTeamPut,
        team_id: str,
        org_id: OrgId,
        request: Request,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        current_group = await self.crud_orgs_teams.get(
            _id=team_id,
            org_id=org_id,
            fields=["ldap_group", "users"],
        )
        if data.ldap_group:
            data.users = await self.crud_ldap.get_logins_from_group(
                group=data.ldap_group
            )
        elif current_group.ldap_group:
            data.users = await self.crud_ldap.get_logins_from_group(
                group=current_group.ldap_group
            )
        return await self.crud_orgs_teams.update(
            _id=team_id,
            org_id=org_id,
            payload=data,
            fields=list(fields),
        )
