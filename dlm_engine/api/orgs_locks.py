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
from dlm_engine.model.orgs import OrgId
from dlm_engine.model.orgs import OrgIdAll
from dlm_engine.model.orgs_locks import filter_list
from dlm_engine.model.orgs_locks import filter_literal
from dlm_engine.model.orgs_locks import sort_literal
from dlm_engine.model.orgs_locks import sort_order_literal
from dlm_engine.model.orgs_locks import OrgLockDelete
from dlm_engine.model.orgs_locks import OrgLockGet
from dlm_engine.model.orgs_locks import OrgLockGetMulti
from dlm_engine.model.orgs_locks import OrgLockId
from dlm_engine.model.orgs_locks import OrgLockPost


class ApiOrgsLocks:
    def __init__(
        self,
        log: logging.Logger,
        authorize: Authorize,
        crud_orgs: CrudOrgs,
        crud_orgs_locks: CrudOrgsLocks,
        crud_orgs_teams: CrudOrgsTeams,
    ):
        self._authorize = authorize
        self._crud_orgs = crud_orgs
        self._crud_orgs_locks = crud_orgs_locks
        self._crud_orgs_teams = crud_orgs_teams
        self._log = log
        self._router = APIRouter(
            prefix="/orgs/{org_id}/locks",
            tags=["orgs_locks"],
        )

        self.router.add_api_route(
            "",
            self.search,
            response_model=OrgLockGetMulti,
            response_model_exclude_unset=True,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.create,
            response_model=OrgLockGet,
            response_model_exclude_unset=True,
            methods=["POST"],
            status_code=201,
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.delete,
            response_model=DataDelete,
            response_model_exclude_unset=True,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/{lock_id}",
            self.get,
            response_model=OrgLockGet,
            response_model_exclude_unset=True,
            methods=["GET"],
        )

    @property
    def authorize(self):
        return self._authorize

    @property
    def crud_orgs(self):
        return self._crud_orgs

    @property
    def crud_orgs_packages(self):
        return self._crud_orgs_locks

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
        data: OrgLockPost,
        lock_id: OrgLockId,
        org_id: OrgId,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_member(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        return await self.crud_orgs_packages.create(
            _id=lock_id,
            org_id=org_id,
            payload=data,
            fields=list(fields),
        )

    @api_version(2)
    async def delete(
        self,
        request: Request,
        data: OrgLockDelete,
        lock_id: OrgLockId,
        org_id: OrgId,
    ):
        await self.authorize.require_org_member(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        await self.crud_orgs_packages.resource_exists(
            _id=lock_id,
            org_id=org_id,
        )
        await self.crud_orgs_packages.delete_mark(
            _id=lock_id,
            org_id=org_id,
        )
        return await self.crud_orgs_packages.delete(
            _id=lock_id,
            org_id=org_id,
        )

    @api_version(2)
    async def get(
        self,
        lock_id: OrgLockId,
        org_id: OrgId,
        request: Request,
        fields: Union[Set[filter_literal], None] = Query(default=filter_list),
    ):
        await self.authorize.require_org_member(request=request, org_id=org_id)
        await self.crud_orgs.resource_exists(_id=org_id)
        return await self.crud_orgs_packages.get(
            _id=lock_id, org_id=org_id, fields=list(fields)
        )

    @api_version(2)
    async def search(
        self,
        request: Request,
        org_id: OrgIdAll,
        package: str = Query(description="filter: regular_expressions", default=None),
        tags: list = Query(description="filter: regular_expressions", default=None),
        disabled: bool = Query(description="filter: boolean", default=None),
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
        if org_id == "_all":
            org_id = None
            user = await self.authorize.require_user(request=request)
            if not user.admin:
                org_filter = await self.crud_orgs_teams.get_all_orgs_from_user(
                    user_id=user.id
                )
        else:
            await self.authorize.require_org_member(request=request, org_id=org_id)
            await self.crud_orgs.resource_exists(_id=org_id)
        return await self.crud_orgs_packages.search(
            _id=package,
            org_id=org_id,
            org_filter=org_filter,
            tags=tags,
            disabled=disabled,
            fields=list(fields),
            sort=sort,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
