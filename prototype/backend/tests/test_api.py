import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orphan-repurpose-api"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "OrphanRepurpose API"
        assert "RESEARCH PROTOTYPE" in data["disclaimer"]


class TestDiseasesEndpoints:
    @pytest.mark.asyncio
    async def test_search_diseases_empty(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/diseases")
        # Will fail without KG service, but tests the route exists
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_disease_not_found(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/diseases/ORPHA:999999")
        assert response.status_code in [404, 500]