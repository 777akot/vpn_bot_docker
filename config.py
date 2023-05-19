from dataclasses import dataclass
from typing import List


@dataclass
class DbConfig:
    host: str
    port: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: List[int]
    ip: str
    port: int

@dataclass
class Webhook:
    url: str

@dataclass
class Yoomoney:
    receiver: str
    price: float
    target: str
    token: str
    host: str

@dataclass
class Key:
    ttl: int
    expiration: int

@dataclass
class Referer:
    payout_percent: int


# CLASSES REGISTRATION:

@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    webhook: Webhook
    yoomoney: Yoomoney
    key: Key
    referer: Referer

def load_config():
    from os import environ
    return Config(
        tg_bot=TgBot(
            token=environ.get("BOT_TOKEN"),
            admin_ids=list(map(int, environ.get("ADMIN").split(","))),
            ip=environ.get('BOT_IP'), port=int(environ.get("BOT_PORT"))
        ),
        db=DbConfig(
            host=environ.get('DB_HOST'),
            password=environ.get('DB_PASS'),
            port=environ.get('DB_PORT'),
            user=environ.get('DB_USER'),
            database=environ.get('DB_NAME')
        ),
        webhook=Webhook(url=environ.get("SERVER_URL")),
        yoomoney=Yoomoney(
            receiver=environ.get("YOOMONEY_RECEIVER"),
            price=environ.get("YOOMONEY_PRICE"),
            target=environ.get("YOOMONEY_TARGET"),
            token=environ.get("YOOMONEY_TOKEN"),
            host=environ.get("YOOMONEY_HOST")
        ),
        key=Key(
            ttl=environ.get("KEY_TTL"),
            expiration=environ.get("KEY_EXPIRATION")
        ),
        referer=Referer(
            payout_percent=environ.get("REFERER_PAYOUT_PERCENT")
        )
    )
