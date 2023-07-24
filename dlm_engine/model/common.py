from pydantic import BaseModel, conint


class MetaMulti(BaseModel):
    result_size: conint(ge=0)


class DataDelete(BaseModel):
    pass
