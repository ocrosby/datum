import pytest
import requests
from unittest.mock import patch, Mock
from index_processor.vendor_detection import determine_vendor

# Mock URLs for testing
WMT_URL = "https://example.com/wmt"
SIDEARM_URL = "https://example.com/sidearm"
PRESTO_URL = "https://example.com/presto"
UNKNOWN_URL = "https://example.com/unknown"
FAILED_URL = "https://example.com/failed"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

@pytest.fixture
def mock_append_to_file():
    with patch('test_index_processor.file_operations.append_to_file') as mock:
        yield mock

@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock:
        yield mock

def test_determine_vendor_wmt(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'some content with ' + WMT_URL
    mock_requests_get.return_value = mock_response

    vendor = determine_vendor(WMT_URL, HEADERS)
    assert vendor == "WMT"

def test_determine_vendor_sidearm(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'some content with sidearmsports.com'
    mock_requests_get.return_value = mock_response

    vendor = determine_vendor(SIDEARM_URL, HEADERS)
    assert vendor == "Sidearm"

def test_determine_vendor_presto(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'some content with prestosports.com'
    mock_requests_get.return_value = mock_response

    vendor = determine_vendor(PRESTO_URL, HEADERS)
    assert vendor == "PrestoSports"

def test_determine_vendor_unknown(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'some content with unknown vendor'
    mock_requests_get.return_value = mock_response

    vendor = determine_vendor(UNKNOWN_URL, HEADERS)
    assert vendor is None
    mock_append_to_file.assert_called_with('unrecognized_vendors.txt', UNKNOWN_URL)

def test_determine_vendor_failed_request(mock_requests_get, mock_append_to_file):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    vendor = determine_vendor(FAILED_URL, HEADERS)
    assert vendor is None
    mock_append_to_file.assert_called_with('failed_requests.txt', FAILED_URL)
