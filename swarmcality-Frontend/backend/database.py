from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings


async def init_db() -> None:
    from models.user import User
    from models.notebook import Notebook
    from models.source import Source
    from models.prompt import GeneratedPrompt

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[User, Notebook, Source, GeneratedPrompt],
    )
