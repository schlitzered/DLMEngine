from typing import List
from typing import Optional
from pydantic import BaseModel
from pydantic import StrictStr

from dlm_engine.model.common import MetaMulti


class OauthProviderGet(BaseModel):
    id: Optional[StrictStr] = None


class OauthProviderGetMulti(BaseModel):
    result: List[OauthProviderGet]
    meta: MetaMulti
