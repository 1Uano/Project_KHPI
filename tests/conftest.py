import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    """
    Фікстура, що надає асинхронного HTTP-клієнта для тестування FastAPI.
    Використовує ASGI Transport — реальний сервер не запускається.
    База даних мокується, тому тести не потребують MongoDB.
    """
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id"))
    mock_collection.list_collection_names = AsyncMock(return_value=["users", "medical_records", "prescriptions"])

    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_db.list_collection_names = AsyncMock(return_value=["users", "medical_records", "prescriptions"])

    mock_motor_client = MagicMock()
    mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

    with patch("app.main.AsyncIOMotorClient", return_value=mock_motor_client), \
         patch("app.database.db.db") as mock_global_db:

        mock_global_db.client = mock_motor_client

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
