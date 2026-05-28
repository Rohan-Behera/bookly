from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from src.config import config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker


engine = AsyncEngine(create_engine(
    url=config.DATABASE_URL,
    echo=True
))

Session = sessionmaker(
    bind = engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        #checks if any new model has been created and takes the metadata and creates the tables in our db
        await conn.run_sync(SQLModel.metadata.create_all)


#Dependency Injection
async def get_session():
    async with Session() as session:
        yield session