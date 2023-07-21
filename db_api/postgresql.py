import asyncio
import logging
from typing import Union, Optional

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool


logger = logging.getLogger(__name__)


class Database:

    def __init__(self, username: str, password: str, host: str, database: str, port: str,
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None):
        self._main_loop = loop
        self.pool: Union[Pool, None] = None
        self._pool: Union[Pool, None] = None
        self._username = username
        self._password = password
        self._host = host
        self._database = database
        self._port = port

    async def create_pool(self):
        self._pool = await asyncpg.create_pool(user=self._username,
                                               password=self._password,
                                               host=self._host,
                                               database=self._database,
                                               port=self._port,
                                               min_size=20,
                                               max_size=40
                                               )
        logger.info("Created asyncpg connection pool")
        return self._pool

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    async def get_pool(self):
        if self._pool is None: self._pool = await self.create_pool()
        if not self._pool._loop.is_running():
            logger.info("Pool is not running in loop")
            await self._pool.close()
            self._pool = await self.create_pool()
        return self._pool

    async def close(self):
        if self._pool: await self._pool.close()

    async def execute(self, command, *args, fetch: bool = False, fetchval: bool = False, fetchrow: bool = False,
                      execute: bool = False):
        if self._pool is None: await self.get_pool()
        async with self._pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
                return result

    async def create_servers_table(self):
        sql = "CREATE TABLE IF NOT EXISTS vpn_servers (" \
              "id bigserial PRIMARY KEY, " \
              "server_name VARCHAR(60) NOT NULL," \
              "api_link VARCHAR(255) NOT NULL UNIQUE," \
              "price INT NOT NULL," \
              "UNIQUE (api_link, server_name))"
        return await self.execute(sql, execute=True)

    async def create_users_table(self):
        sql = "CREATE TABLE IF NOT EXISTS vpn_users (" \
              "id bigserial PRIMARY KEY, " \
              "user_id bigserial NOT NULL UNIQUE," \
              "user_name VARCHAR(60) NOT NULL," \
              "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()," \
              "role VARCHAR(60) NOT NULL DEFAULT 'user'," \
              "trial_used BOOLEAN DEFAULT FALSE," \
              "bought BOOLEAN DEFAULT FALSE," \
              "referer_id bigserial," \
              "referal_role VARCHAR(60) NOT NULL DEFAULT 'inviter'," \
              "user_account VARCHAR(255)," \
              "free_months INT DEFAULT 0," \
              "UNIQUE (user_id))"
        return await self.execute(sql, execute=True)
    
    async def create_keys_table(self):
        sql = "CREATE TABLE IF NOT EXISTS vpn_keys (" \
              "id bigserial PRIMARY KEY, " \
              "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()," \
              "bought BOOLEAN DEFAULT FALSE," \
              "owner_id bigserial NOT NULL," \
              "label VARCHAR(255) NOT NULL," \
              "expiration_at TIMESTAMPTZ NOT NULL," \
              "active BOOLEAN DEFAULT FALSE," \
              "server_id INT NOT NULL," \
              "outline_key_id INT," \
              "outline_access_url VARCHAR(255)," \
              "UNIQUE (id, label, outline_key_id, outline_access_url))"
        return await self.execute(sql, execute=True)

    async def create_payments_table(self):
        sql = "CREATE TABLE IF NOT EXISTS vpn_payments (" \
              "id bigserial PRIMARY KEY, " \
              "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()," \
              "label VARCHAR(255) NOT NULL," \
              "user_id bigserial NOT NULL," \
              "referer_id bigserial," \
              "sum INT NOT NULL," \
              "sum_paid BOOLEAN DEFAULT FALSE," \
              "referer_payout INT DEFAULT 0," \
              "referer_payout_paid BOOLEAN DEFAULT FALSE," \
              "UNIQUE (id))"
        return await self.execute(sql, execute=True)

    # SERVERS #

    async def get_servers(self):
        sql = "SELECT (id, server_name) FROM vpn_servers"
        return await self.execute(sql, fetch=True)
    
    async def get_server_by_id(self, server_id):
        sql = "SELECT (id, server_name, price) FROM vpn_servers WHERE id = $1"
        return await self.execute(sql, server_id, fetch=True)

    async def get_server_key(self, server_id):
        sql = "SELECT api_link FROM vpn_servers WHERE id=$1"
        return await self.execute(sql, server_id, fetchval=True)

    async def add_server(self, server_name, api_link, price):
        sql = "INSERT INTO vpn_servers (server_name, api_link, price) VALUES ($1, $2, $3)"
        return await self.execute(sql, server_name, api_link, price, execute=True)

    async def delete_server(self, server_id):
        sql = "DELETE FROM vpn_servers WHERE id=$1"
        return await self.execute(sql, server_id, execute=True)

    # USERS #

    async def add_user(self, user_id, user_name, referer_id):
        sql = "INSERT INTO vpn_users (user_id, user_name, referer_id) VALUES ($1, $2, $3)"
        return await self.execute(sql, user_id, user_name, referer_id, execute=True)
    
    async def get_user_by_id(self, user_id):
        sql = "SELECT * FROM vpn_users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch=True)
    
    async def check_trial(self, user_id):
        sql = "SELECT (trial_used) FROM vpn_users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetchval=True)
    
    async def update_user_payment_status(self, user_id, bought):
        sql = "UPDATE vpn_users SET bought=($2) WHERE user_id=($1)"
        return await self.execute(sql, user_id, bought, execute=True)

    async def set_trial_used(self, user_id, trial_used):
        sql = "UPDATE vpn_users SET trial_used=($2) WHERE user_id = $1"
        return await self.execute(sql, user_id, trial_used, execute=True)
    
    async def show_users(self):
        sql = "SELECT * FROM vpn_users ORDER BY created_at DESC"
        return await self.execute(sql, fetch=True)
    
    async def update_free_months(self, user_id, amount):
        sql = "UPDATE vpn_users SET free_months = free_months + $2 WHERE user_id = $1"
        return await self.execute(sql, user_id, amount, execute=True)

    # KEYS #

    async def get_all_labels(self):
        sql = "SELECT (label) FROM vpn_keys"
        return await self.execute(sql, fetch=True)

    async def add_key(self, owner_id, label, expiration_at, server_id):
        sql = "INSERT INTO vpn_keys (owner_id, label, expiration_at, server_id) VALUES ($1, $2, $3, $4)"
        return await self.execute(sql, owner_id, label, expiration_at, server_id, execute=True)
    
    async def get_all_keys(self, user_id):
        sql = "SELECT (server_id,active,bought,label,outline_key_id,expiration_at) FROM vpn_keys WHERE owner_id = $1 ORDER BY created_at DESC"
        return await self.execute(sql, user_id, fetch=True)
    
    async def get_all_keys_data(self):
        sql = "SELECT * FROM vpn_keys"
        return await self.execute(sql, fetch=True)
    
    async def get_key_by_label(self, label):
        sql = "SELECT (outline_access_url) FROM vpn_keys WHERE label=$1"
        return await self.execute(sql, label, fetchval=True)
    
    async def get_key_all_data_by_label(self, label):
        sql = "SELECT * FROM vpn_keys WHERE label=$1"
        return await self.execute(sql, label, fetch=True)

    async def get_key_data_by_label(self, label):
        sql = "SELECT (server_id, outline_key_id) FROM vpn_keys WHERE label=$1"
        return await self.execute(sql, label, fetchval=True)
    
    async def delete_key(self, key_id, server_id):
        sql = "DELETE FROM vpn_keys WHERE label=$1 AND server_id=$2"
        return await self.execute(sql, key_id, server_id, execute=True)

    async def update_key(self, key_id, label):
        sql = "UPDATE vpn_keys SET label=($2) WHERE key_id=($1)"
        return await self.execute(sql, key_id, label, execute=True)
    
    async def get_payment_status(self, user_id, label):
        sql = "SELECT (label,bought) FROM vpn_keys WHERE owner_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, fetchval=True)
    
    async def update_payment_status(self, user_id, label, bought):
        sql = "UPDATE vpn_keys SET bought=($3), active=($3) WHERE owner_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, bought, execute=True)
    
    async def update_outline_key_id(self, user_id, label, key_id, access_url):
        sql = "UPDATE vpn_keys SET outline_key_id=($3), outline_access_url=($4) WHERE owner_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, key_id, access_url, execute=True)
    
    async def get_outline_key(self, user_id, label):
        sql = "SELECT (outline_key_id, outline_access_Url) FROM vpn_keys WHERE owner_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, fetchval=True)
    
    async def set_key_active(self, key_id, label, active):
        sql = "UPDATE vpn_keys SET active=($3) WHERE outline_key_id=($1) AND label=($2)"
        return await self.execute(sql, key_id, label, active, execute=True)
    
    async def update_key_expiration(self, key_id, label, expiration):
        sql = "UPDATE vpn_keys SET expiration_at=($3), active=True, bought=True WHERE outline_key_id=($1) AND label=($2)"
        return await self.execute(sql, key_id, label, expiration, execute=True)
    
    # REFERALS

    async def get_referal_users(self, user_id):
        sql = "SELECT (bought) FROM vpn_users WHERE referer_id=($1)"
        return await self.execute(sql, user_id, fetch=True)
    
    async def check_referal(self, user_id, referal_role):
        sql = "SELECT * FROM vpn_users WHERE user_id=($1) AND referal_role=($2)"
        return await self.execute(sql, user_id, referal_role, fetch=True)
    
    async def add_partner(self, user_id, referal_role):
        sql = "UPDATE vpn_users SET referal_role=($2) WHERE user_id=($1)"
        return await self.execute(sql, user_id, referal_role, execute=True)
    
    async def add_account(self, user_id, user_account):
        sql = "UPDATE vpn_users SET user_account=($2) WHERE user_id=($1)"
        return await self.execute(sql, user_id, user_account, execute=True)
    

    # PAYMENTS

    async def add_payment(self, label, user_id, referer_id, sum, referer_payout):
        sql = "INSERT INTO vpn_payments (label, user_id, referer_id, sum, referer_payout) VALUES ($1, $2, $3, $4, $5) RETURNING id, label, user_id, referer_id, sum, referer_payout"
        return await self.execute(sql, label, user_id, referer_id, sum, referer_payout, fetchrow=True)
    
    async def get_all_payments(self):
        sql = "SELECT (label, user_id) from vpn_payments"
        return await self.execute(sql, fetch=True)

    async def get_payment_by_id(self, label, user_id):
        sql = "SELECT * FROM vpn_payments WHERE label=$1 AND user_id=$2 ORDER BY created_at DESC"
        return await self.execute(sql, label, user_id, fetch=True)
    
    async def get_payment_by_payment_id(self, user_id, label, payment_id):
        sql = "SELECT * FROM vpn_payments WHERE label=$2 AND user_id=$1 AND id=$3 ORDER BY created_at DESC"
        return await self.execute(sql, user_id, label, payment_id, fetch=True)

    async def get_payment_by_referer_id(self, referer_id):
        sql = "SELECT (sum, referer_payout) FROM vpn_payments WHERE referer_id=$1 AND referer_payout_paid='True'"
        return await self.execute(sql, referer_id, fetch=True)
    
    async def update_payment_status_by_id(self, user_id, label, sum_paid):
        sql = "UPDATE vpn_payments SET sum_paid=($3) WHERE user_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, sum_paid, execute=True)
    
    async def update_payment_trial(self, user_id, label):
        sql = "UPDATE vpn_payments SET sum=0, referer_payout=0 WHERE user_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, execute=True)
    
    async def update_payment_referer_status_by_id(self, user_id, label, referer_payout_paid):
        sql = "UPDATE vpn_payments SET referer_payout_paid=($3) WHERE user_id=($1) AND label=($2)"
        return await self.execute(sql, user_id, label, referer_payout_paid, execute=True)

    async def delete_payment_by_label(self, user_id, label):
        sql = "DELETE FROM vpn_payments WHERE user_id=$1 AND label=$2"
        return await self.execute(sql, user_id, label, execute=True)