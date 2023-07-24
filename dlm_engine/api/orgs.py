import logging
from typing import Set
from typing import Union

from fastapi import APIRouter
from fastapi import Query
from fastapi import Request
from fastapi_versionizer import api_version

from dlm_engine.authorize import Authorize

from dlm_engine.crud.orgs import CrudOrgs
from dlm_engine.crud.orgs_locks import CrudOrgsLocks
from dlm_engine.crud.orgs_teams import CrudOrgsTeams

from dlm_engine.model.common import DataDelete
from dlm_engine.model.orgs import filter_list
from dlm_engine.model.orgs import filter_literal
from dlm_engine.model.orgs import sort_literal
from dlm_engine.model.orgs import sort_order_literal
from dlm_engine.model.orgs import OrgId
from dlm_engine.model.orgs import OrgGet
from dlm_engine.model.orgs import OrgGetMulti
from dlm_engine.model.orgs import OrgPost
from dlm_engine.model.orgs import OrgPut
from dlm_engine.model.orgs_teams import OrgTeamPost


class ApiOrgs:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_orgs: CrudOrgs,
        crud_orgs_packages: CrudOrgsLocks,
        crud_orgs_teams: CrudOrgsTeams,
    ):
        self._authorize = authorize
        self._crud_orgs = crud_orgs
        self._crud_orgs_packages = crud_orgs_packages
        self._crud_orgs_teams = crud_orgs_teams
        self._log = log
        self._router = APIRouter(
            prefix="/orgs",
            tags=["orgs"],
        )

        self.router.add_api_route(
            "",
            self.search,
            response_model=OrgGetMulti,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{org_id}",
            self.create,
            response_model=OrgGet,
            response_model_exclude_unset=True,
            methods=["POST"],
            status_code=201,
        )
        self.router.add_api_route(
            "/{org_id}",
            self.delete,
            response_model=DataDelete,
            response_model_exclude_unset=True,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/{org_id}",
            self.get,
            response_model=OrgGet,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{org_id}",
            self.update,
            response_model=OrgGet,
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
    def crud_orgs_packages(self):
        return self._crud_orgs_packages

    @property
    def crud_orgs_teams(self):
        return self._crud_orgs_teams

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
        data: OrgPost,
        org_id: OrgId,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        user = await self.authorize.get_user(request=request)
        result = await self.crud_orgs.create(
            _id=org_id, payload=data, fields=list(fields)
        )
        team = OrgTeamPost(org_admin=True, users=[user.id])
        await self.crud_orgs_teams.create(
            _id="default", org_id=org_id, payload=team, fields=[]
        )
        return result

    @api_version(2)
    async def delete(
        self,
        request: Request,
        org_id: OrgId,
    ):
        await self.authorize.require_admin(request=request)
        await self.crud_orgs.delete_mark(_id=org_id)
        await self.crud_orgs_packages.delete_all_from_org(org_id=org_id)
        await self.crud_orgs_teams.delete_all_from_org(org_id=org_id)
        return await self.crud_orgs.delete(_id=org_id)

    @api_version(2)
    async def get(
        self,
        org_id: OrgId,
        request: Request,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_member(request=request, org_id=org_id)
        return await self.crud_orgs.get(_id=org_id, fields=list(fields))

    @api_version(2)
    async def search(
        self,
        request: Request,
        org_id: str = Query(description="filter: regular_expressions", default=None),
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
        org_filter = None
        user = await self.authorize.require_user(request=request)
        if not user.admin:
            org_filter = await self.crud_orgs_teams.get_all_orgs_from_user(
                user_id=user.id
            )
        return await self.crud_orgs.search(
            _id=org_id,
            _id_filter=org_filter,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )

    @api_version(2)
    async def update(
        self,
        data: OrgPut,
        org_id: OrgId,
        request: Request,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_admin(request=request, org_id=org_id)
        return await self.crud_orgs.update(
            _id=org_id, payload=data, fields=list(fields)
        )
