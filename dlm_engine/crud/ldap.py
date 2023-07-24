import asyncio
import logging
from typing import Optional

import bonsai.asyncio
import bonsai.errors
import bonsai.pool

from dlm_engine.errors import LdapInvalidDN
from dlm_engine.errors import LdapResourceNotFound
from dlm_engine.errors import LdapNoBackend


class CrudLdap:
    def __init__(
        self,
        log: logging.Logger,
        pool: Optional[bonsai.asyncio.AIOConnectionPool] = None,
    ):
        self._log = log
        self._pool = pool

    @property
    def log(self):
        return self._log

    @property
    def pool(self):
        if not self._pool:
            raise LdapNoBackend
        return self._pool

    async def _ldap_search(
        self,
        base_dn: str,
        scope: bonsai.LDAPSearchScope,
        query: str,
    ):
        counter = self.pool.max_connection + 3
        while counter >= 0:
            conn = await self.pool.get()
            try:
                return await conn.search(base_dn, scope, query)
            except bonsai.pool.EmptyPool:
                self.log.warning("ldap pool empty, waiting 1 second")
                await asyncio.sleep(1)
            except bonsai.errors.ConnectionError:
                conn.close()
                if counter == 0:
                    self.log.error("lost ldap connection, no more retries left")
                else:
                    self.log.error(f"lost ldap connection, {counter} retries left")
                    counter -= 1
            finally:
                await self.pool.put(conn)

    async def get_login(self, user: str):
        user_cn, user_base = user.split(",", maxsplit=1)
        user = await self._ldap_search(
            base_dn=user_base, scope=bonsai.LDAPSearchScope.ONELEVEL, query=user_cn
        )
        return user[0]["sAMAccountName"]

    async def get_logins_from_group(self, group: str):
        try:
            group_cn, group_base = group.split(",", maxsplit=1)
        except ValueError:
            raise LdapInvalidDN
        ldap_group = await self._ldap_search(
            base_dn=group_base, scope=bonsai.LDAPSearchScope.ONELEVEL, query=group_cn
        )
        try:
            ldap_group = ldap_group[0]
        except IndexError:
            raise LdapResourceNotFound
        jobs = []
        for user in ldap_group["member"]:
            jobs.append(asyncio.create_task(self.get_login(user=user)))
        if not jobs:
            self.log.warning(f"ldap group has no members: {group}")
            return []
        done, _ = await asyncio.wait(jobs, return_when=asyncio.ALL_COMPLETED)
        logins = []
        for job in done:
            logins.append(job.result()[0])
        return logins
