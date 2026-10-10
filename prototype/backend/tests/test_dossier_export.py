"""PDF export must not return HTML as a downloadable PDF."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.dossier_service import DossierService


def test_pdf_renderer_failure_does_not_return_html(monkeypatch) -> None:
    renderer = Mock(side_effect=RuntimeError("PDF renderer unavailable"))
    monkeypatch.setitem(sys.modules, "weasyprint", SimpleNamespace(HTML=renderer))
    assert DossierService()._html_to_pdf("<html>Research dossier</html>") == b""
