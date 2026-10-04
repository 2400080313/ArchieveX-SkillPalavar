"""
Unit tests for ArchiveX Copilot & Rule-based Archive Assistant
"""
import pytest
from core.copilot import ArchiveCopilot

def test_copilot_deterministic_labeling():
    """When no LLM API key is passed, engine mode must be 'Rule-based Archive Assistant'."""
    copilot = ArchiveCopilot(api_key=None)
    assert copilot.engine_mode == "Rule-based Archive Assistant"
    assert not copilot.is_llm_active()

def test_copilot_exact_prompt_query():
    """Verify exact natural-language response mandated by specification."""
    copilot = ArchiveCopilot(api_key=None)
    context = {
        "Key": "backups/postgres/2023_prod.dump",
        "AgeDays": 412,
        "StorageClass": "S3 Standard",
        "Size": 10 * 1024 * 1024 * 1024
    }
    query = "Why should I archive this backup?"
    response = copilot.answer_query(query, context=context)

    expected = (
        "Because it is 412 days old, currently stored in S3 Standard, and its available metadata "
        "indicates it is a strong long-term archive candidate. Access frequency is unavailable, "
        "so this recommendation should be reviewed before applying changes."
    )
    assert response == expected

def test_copilot_small_object_query():
    copilot = ArchiveCopilot(api_key=None)
    resp = copilot.answer_query("Why not move small files to Glacier?")
    assert "128 KB" in resp
    assert "minimum billable size" in resp.lower()

def test_copilot_intelligent_tiering_query():
    copilot = ArchiveCopilot(api_key=None)
    resp = copilot.answer_query("Why was Intelligent-Tiering recommended?")
    assert "retrieval fees" in resp.lower()
    assert "$0.0025" in resp
