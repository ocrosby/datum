import pytest
from unittest.mock import patch, mock_open
from index_processor.file_operations import append_to_text_file, read_from_file

@pytest.fixture
def mock_open_file():
    with patch('builtins.open', mock_open()) as mock:
        yield mock

def test_append_to_file(mock_open_file):
    append_to_text_file('test_file.txt', 'test content')
    mock_open_file.assert_called_once_with('test_file.txt', 'a')
    mock_open_file().write.assert_called_once_with('test content\n')

def test_read_from_file(mock_open_file):
    mock_open_file.return_value.read.return_value = 'line1\nline2\nline3\n'
    result = read_from_file('test_file.txt')
    assert result == ['line1', 'line2', 'line3']
    mock_open_file.assert_called_once_with('test_file.txt', 'r')
