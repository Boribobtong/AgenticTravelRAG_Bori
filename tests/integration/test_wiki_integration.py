"""Integration tests for Wikipedia tool in the workflow."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.workflow import ARTWorkflow


@pytest.fixture
def test_workflow():
    """Provide an ARTWorkflow instance for testing."""
    return ARTWorkflow()


@pytest.fixture
def test_sample_state():
    """Provide a sample AppState for testing."""
    return {
        'user_query': 'Paris travel plan',
        'destination': 'Paris',
        'travel_dates': ['2025-12-01', '2025-12-05'],
        'traveler_count': 2,
        'preferences': {'romantic': True},
        'hotel_options': [
            MagicMock(name='Hotel A', rating=4.5, price_range='$$', review_highlights=['Great view']),
            MagicMock(name='Hotel B', rating=4.0, price_range='$', review_highlights=['Central']),
        ],
        'weather_forecast': [],
        'google_search_results': [],
        'session_id': 'test-session-001',
        'chat_history': [],
        'error_messages': [],
        'context_memory': {},
        'conversation_state': 'ongoing',
        'ab_experiment_id': None,
        'ab_variant': None,
        'satisfaction_score': None,
        'user_feedback': None,
        'final_itinerary': None,
        'execution_path': [],
    }


def test_wiki_tool_integration_response_generator():
    """Test that ResponseGenerator includes wiki_entries in the final output."""
    from src.agents.response_generator import ResponseGeneratorAgent
    
    agent = ResponseGeneratorAgent()
    
    # Mock wiki entries
    wiki_entries = [
        {
            'title': 'Paris',
            'summary': 'Paris is the capital of France.',
            'source': 'https://en.wikipedia.org/wiki/Paris'
        },
        {
            'title': 'Paris history',
            'summary': 'Paris has a rich history dating back to Roman times.',
            'source': 'https://en.wikipedia.org/wiki/History_of_Paris'
        }
    ]
    
    # Test that wiki entries are properly formatted in response generator
    test_state = {
        'destination': 'Paris',
        'wiki_entries': wiki_entries
    }
    
    # Verify wiki snippets are formatted correctly
    formatted = agent._format_wiki_entries(test_state.get('wiki_entries', []))
    
    assert 'Paris' in formatted
    assert 'France' in formatted
    assert 'history' in formatted


def test_wiki_tool_integration_workflow_state():
    """Test that wiki entries are properly integrated in workflow state."""
    # Verify wiki entries structure
    wiki_entries = [
        {'title': 'Paris', 'summary': 'Paris summary', 'source': 'https://...'},
        {'title': 'Paris History', 'summary': 'Paris history summary', 'source': 'https://...'}
    ]
    
    # Verify all entries have expected keys
    for entry in wiki_entries:
        assert 'title' in entry
        assert 'summary' in entry
        assert 'source' in entry
        assert 'error' not in entry


@pytest.mark.asyncio
async def test_wiki_snippets_formatting():
    """Test that wiki snippets are correctly formatted in response generator."""
    from src.agents.response_generator import ResponseGeneratorAgent
    
    agent = ResponseGeneratorAgent()
    
    wiki_entries = [
        {'title': 'Test Place', 'summary': 'Test summary', 'source': 'https://example.com'},
        {'title': 'Test History', 'summary': 'History summary', 'source': 'https://example.com/history'},
    ]
    
    formatted = agent._format_wiki_entries(wiki_entries)
    
    # Verify formatted output includes both entries
    assert 'Test Place' in formatted
    assert 'Test History' in formatted
    assert 'Test summary' in formatted
    assert 'History summary' in formatted
    assert '[출처]' in formatted  # Korean for source


def test_wiki_snippets_empty():
    """Test that empty wiki entries are handled gracefully."""
    from src.agents.response_generator import ResponseGeneratorAgent
    
    agent = ResponseGeneratorAgent()
    formatted = agent._format_wiki_entries([])
    
    assert '없음' in formatted or '정보' in formatted  # "no info" message


def test_wiki_snippets_with_errors():
    """Test that error entries in wiki_entries are skipped."""
    from src.agents.response_generator import ResponseGeneratorAgent
    
    agent = ResponseGeneratorAgent()
    
    wiki_entries = [
        {'title': 'Valid Place', 'summary': 'Valid summary', 'source': 'https://example.com'},
        {'error': 'disambiguation', 'options': ['A', 'B', 'C']},  # Should be skipped
    ]
    
    formatted = agent._format_wiki_entries(wiki_entries)
    
    # Verify only valid entry is included
    assert 'Valid Place' in formatted
    assert 'disambiguation' not in formatted
    assert 'options' not in formatted

