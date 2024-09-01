import pytest

from index import google_search, is_url_womens_soccer, is_url_mens_soccer, determine_vendor, HEADERS

@pytest.mark.parametrize("search_query, expected_condition", [
    ('Wichita State University Soccer', lambda results: len(results) > 0),
    ('Nonexistent University Soccer', lambda results: len(results) > 0)
    # Add more test cases as needed
])
def test_google_search(search_query, expected_condition):
    search_results = google_search(search_query)
    assert expected_condition(search_results), f"Failed for query: {search_query}"


@pytest.mark.parametrize("url, expected_answer", [
    ('https://tulanegreenwave.com/sports/womens-soccer', True),
])
def test_is_url_womens_soccer(url, expected_answer):
    assert is_url_womens_soccer(url) == expected_answer

@pytest.mark.parametrize("url, expected_answer", [
    ('https://tulanegreenwave.com/sports/womens-soccer', False),
])
def test_is_url_mens_soccer(url, expected_answer):
    assert is_url_mens_soccer(url) == expected_answer


@pytest.mark.parametrize('url, expected_vendor', [
    ('https://andrewfightingtigers.com/sports/msoc/2024-25/releases/20240831pdqnga', 'PrestoSports')
 ])
def test_determine_vendor(url, expected_vendor):
    assert determine_vendor(url, headers=HEADERS) == expected_vendor
