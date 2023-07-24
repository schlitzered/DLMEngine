import typing

from pydantic import ConfigDict
from pydantic import BaseModel
from pydantic import BaseSettings

log_levels = typing.Literal[
    "CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"
]


class Ldap(BaseModel):
    url: typing.Optional[str] = None
    binddn: typing.Optional[str] = None
    password: typing.Optional[str] = None


class OAuthClient(BaseModel):
    id: str
    secret: str


class OAuthUrl(BaseModel):
    authorize: str
    accesstoken: str
    userinfo: typing.Optional["str"] = None


class OAuth(BaseModel):
    scope: str
    type: str
    client: OAuthClient
    url: OAuthUrl


class Settings(BaseSettings):
    app_loglevel: log_levels = "INFO"
    ldap: Ldap = Ldap()
    mongodb_main_url: str = "mongodb://localhost:27017"
    mongodb_main_database: str = "dlm_engine"
    session_secret_key: str
    oauth: dict[str, OAuth] = dict()
    model_config = ConfigDict(env_file=".env", env_nested_delimiter="_")
