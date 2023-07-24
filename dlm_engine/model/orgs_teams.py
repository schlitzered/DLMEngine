from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from pydantic import StrictStr
from pydantic import StrictBool

from dlm_engine.model.common import MetaMulti
from dlm_engine.model.orgs import OrgId

filter_literal = Literal[
    "id",
    "ldap_group",
    "org_admin",
    "org",
    "permissions",
    "users",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal["id"]
sort_order_literal = Literal[
    "ascending",
    "descending",
]


class OrgTeamGet(BaseModel):
    id: Optional[StrictStr] = None
    ldap_group: Optional[StrictStr] = ""
    org: Optional[OrgId] = None
    org_admin: Optional[StrictBool] = None
    permissions: Optional[List[StrictStr]] = None
    users: Optional[List[StrictStr]] = None


class OrgTeamGetMulti(BaseModel):
    result: List[OrgTeamGet]
    meta: MetaMulti


class OrgTeamPost(BaseModel):
    ldap_group: Optional[StrictStr] = ""
    org_admin: Optional[StrictBool] = False
    users: Optional[List[StrictStr]] = []


class OrgTeamPut(BaseModel):
    ldap_group: Optional[StrictStr] = None
    org_admin: Optional[StrictBool] = None
    users: Optional[List[StrictStr]] = None
