import redis.asyncio as redis
from src.config import Config
import fakeredis.aioredis as fakeredis

if Config.TESTING:
    redis_client = fakeredis.FakeRedis()
else:
    redis_client = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=0,
        decode_responses=True
    )

# Add to token to black list(JWTid's is used)
async def add_jti_to_blocklist(jti: str) -> None:
    await redis_client.set(name=jti, value="", ex=Config.JTI_EXPIRY)

# check if token is present in blacklist(JWTid's is used)
async def token_in_blocklist(jti: str) -> bool:
    token = await redis_client.get(jti)
    return token is not None

#admin
[
    "adding users",
    "change roles",
    "crud on users",
    "book submission",
    "crud on reviews",
    "revoking access"
]

#users
[
    "crud on their own book submission", "crud on their reviews", "crud on their own accounts"
]