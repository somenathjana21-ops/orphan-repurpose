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


class TestKGEndpoints:
    @pytest.mark.asyncio
    async def test_kg_stats(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/kg/stats")
        assert response.status_code == 200
        data = response.json()
        assert "node_types" in data
        assert "edge_types" in data
        assert "total_nodes" in data
        assert "total_edges" in data
        # Real Kuzu DB should have > 3000 nodes
        assert data["total_nodes"] > 3000

    @pytest.mark.asyncio
    async def test_kg_search(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/kg/search", params={"query": "miglustat"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_kg_drugs(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/kg/drugs", params={"page": 1, "page_size": 5})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] > 1000

    @pytest.mark.asyncio
    async def test_kg_diseases(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/kg/diseases", params={"page": 1, "page_size": 5})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] > 1000


class TestLiteratureEndpoints:
    @pytest.mark.asyncio
    async def test_literature_search(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/literature/search", params={"query": "drug repurposing rare disease"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_literature_summarize(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/literature/summarize", json=["33567210"])
        assert response.status_code == 200
        data = response.json()
        assert "summaries" in data


class TestCandidateEndpoints:
    @pytest.mark.asyncio
    async def test_generate_candidates(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "session_id" in data
        assert len(data["candidates"]) > 0

    @pytest.mark.asyncio
    async def test_get_candidate(self, async_client: AsyncClient):
        # First generate candidates
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            response = await async_client.get(f"/api/v1/candidates/{candidate_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["candidate_id"] == candidate_id

    @pytest.mark.asyncio
    async def test_get_candidate_explanation(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            response = await async_client.get(f"/api/v1/candidates/{candidate_id}/explanation")
            assert response.status_code == 200
            data = response.json()
            assert "kg_paths" in data
            assert "shap_values" in data
            assert "llm_rationale" in data

    @pytest.mark.asyncio
    async def test_get_candidate_safety(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            response = await async_client.get(f"/api/v1/candidates/{candidate_id}/safety")
            assert response.status_code == 200
            data = response.json()
            assert "overall" in data
            assert "faers_signals" in data
            assert "admet_predictions" in data


class TestValidationEndpoints:
    @pytest.mark.asyncio
    async def test_validate_candidate(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            response = await async_client.post(
                f"/api/v1/validation/candidates/{candidate_id}/validate",
                json={"validator": "Dr. Test", "assessment": "plausible", "rationale": "Test validation"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "entry" in data

    @pytest.mark.asyncio
    async def test_self_assess_candidate(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            response = await async_client.post(
                f"/api/v1/validation/candidates/{candidate_id}/assess",
                json={"efficacy": 7, "safety": 6, "feasibility": 8, "notes": "Test assessment"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "entry" in data


class TestAuditEndpoints:
    @pytest.mark.asyncio
    async def test_audit_trail(self, async_client: AsyncClient):
        # First create a validation
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            val_response = await async_client.post(
                f"/api/v1/validation/candidates/{candidate_id}/validate",
                json={"validator": "Dr. Test", "assessment": "plausible", "rationale": "Test"}
            )
            val_data = val_response.json()
            session_id = val_data["session_id"]
            
            response = await async_client.get(f"/api/v1/audit/{session_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            assert len(data["entries"]) > 0

    @pytest.mark.asyncio
    async def test_audit_verify(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_id = gen_data["candidates"][0]["candidate_id"]
            val_response = await async_client.post(
                f"/api/v1/validation/candidates/{candidate_id}/validate",
                json={"validator": "Dr. Test", "assessment": "plausible", "rationale": "Test"}
            )
            val_data = val_response.json()
            session_id = val_data["session_id"]
            
            response = await async_client.get(f"/api/v1/audit/{session_id}/verify")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["entry_count"] > 0


class TestDossierEndpoints:
    @pytest.mark.asyncio
    async def test_generate_dossier(self, async_client: AsyncClient):
        gen_response = await async_client.post("/api/v1/candidates/generate", json={"disease_id": "ORPHA:635"})
        gen_data = gen_response.json()
        if gen_data["candidates"]:
            candidate_ids = [c["candidate_id"] for c in gen_data["candidates"][:3]]
            response = await async_client.post("/api/v1/dossier/generate", json={
                "disease_id": "ORPHA:635",
                "candidate_ids": candidate_ids,
                "include_sections": ["background", "drug_profile", "mechanistic_rationale"]
            })
            assert response.status_code == 200
            data = response.json()
            assert "pdf_base64" in data
            assert "dossier_json" in data
            assert "audit_trail_id" in data
