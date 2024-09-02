import pytest
from unittest.mock import patch, Mock
from index_processor.school_record import process_school_record

# Mock data for testing
SCHOOL_RECORD = {
    "name": "Test School",
    "url": "https://example.com/testschool",
    "vendor": "WMT"
}

@pytest.fixture
def mock_append_to_file():
    with patch('index_processor.file_operations.append_to_file') as mock:
        yield mock

@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock:
        yield mock

def test_process_school_record_success(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'some content with ' + SCHOOL_RECORD["url"]
    mock_requests_get.return_value = mock_response

    result = process_school_record(SCHOOL_RECORD)
    assert result == "Success"

def test_process_school_record_failure(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    result = process_school_record(SCHOOL_RECORD)
    assert result == "Failure"
    mock_append_to_file.assert_called_with('failed_requests.txt', SCHOOL_RECORD["url"])