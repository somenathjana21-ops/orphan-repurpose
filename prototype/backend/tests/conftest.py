import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import pytest
from app.main import app
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_kg_service():
    """Mock KG service for testing."""
    from unittest.mock import Mock
    mock = Mock()
    mock.search_diseases.return_value = ([], 0)
    mock.get_disease.return_value = None
    return mock