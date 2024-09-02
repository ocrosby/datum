import pytest
from unittest.mock import patch, Mock
from index_processor.search import google_search

# Mock data for testing
SEARCH_QUERY = "Test School"
SEARCH_RESULTS = [
    {"name": "Test School", "url": "https://example.com/testschool", "vendor": "WMT"},
    {"name": "Another School", "url": "https://example.com/anotherschool", "vendor": "Sidearm"}
]

@pytest.fixture
def mock_read_from_file():
    with patch('index_processor.file_operations.read_from_file') as mock:
        yield mock

def test_search_records_found(mock_read_from_file):
    mock_read_from_file.return_value = SEARCH_RESULTS
    results = google_search(SEARCH_QUERY)
    assert len(results) == 1
    assert results[0]["name"] == "Test School"

def test_search_records_not_found(mock_read_from_file):
    mock_read_from_file.return_value = SEARCH_RESULTS
    results = google_search("Nonexistent School")
    assert len(results) == 0
