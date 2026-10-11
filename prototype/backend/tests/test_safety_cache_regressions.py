"""Safety assessments must respect supplied evidence and current molecular inputs."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.safety_service import SafetyService


@pytest.fixture
def safety_service():
    service = SafetyService()
    service.admet_predictor = Mock()
    service.admet_predictor.predict.return_value = {"hERG": 0.1}
    service.admet_predictor.overall_safety.return_value = "pass"
    service.admet_predictor.classify_safety.return_value = {"hERG": "pass"}
    service._faers_service = Mock()
    service._faers_service.get_faers_data = AsyncMock(return_value={})
    return service


async def test_explicit_empty_reports_do_not_fetch_remote_evidence(safety_service):
    await safety_service.assess_drug("drug:1", "Drug", "CCO", faers_reports=[])
    safety_service._faers_service.get_faers_data.assert_not_awaited()


async def test_omitted_reports_still_fetch_remote_evidence(safety_service):
    await safety_service.assess_drug("drug:1", "Drug", "CCO")
    safety_service._faers_service.get_faers_data.assert_awaited_once_with("Drug")


async def test_faers_results_are_available_to_cached_readers(safety_service):
    signal = Mock(
        event="Nausea",
        meddra_pt="Nausea",
        ror=2.0,
        prr=1.8,
        bcpnn_ic=0.3,
        n_reports=10,
        level="caution",
    )
    safety_service._analyze_faers = Mock(return_value=[signal])
    await safety_service.assess_drug("drug:1", "Drug", "CCO", faers_reports=[{}])
    assert safety_service.get_faers_signals("drug:1") == [signal]
    safety_service._analyze_faers.return_value = []
    await safety_service.assess_drug("drug:1", "Drug", "CCO", faers_reports=[])
    assert safety_service.get_faers_signals("drug:1") == []


def test_admet_recomputes_when_structure_changes(safety_service):
    safety_service.admet_predictor.predict.side_effect = [{"hERG": 0.1}, {"hERG": 0.8}]
    assert safety_service._predict_admet("drug:1", "") == {"hERG": 0.1}
    assert safety_service._predict_admet("drug:1", "CCO") == {"hERG": 0.8}
    assert safety_service._predict_admet("drug:1", "CCO") == {"hERG": 0.8}
    assert safety_service.admet_predictor.predict.call_count == 2
    assert safety_service.get_admet_predictions("drug:1") == {"hERG": 0.8}
    safety_service.clear_cache()
    assert safety_service.get_admet_predictions("drug:1") is None
