import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import List, Optional

from index_processor.constants import HEADERS
from index_processor.http_operations import send_request_with_rate_limit_handling

filter_substrings = {
    'google.com', 'facebook.com', 'twitter.com', 'instagram.com', 'wikipedia.org',
    'ncsasports.org', 'hudl.com', 'youtube.com', 'coaches', 'sportsrecruits.com',
    'reddit.com', 'staff-directory', 'basketball', 'baseball', 'softball', 'volleyball',
    'club-soccer', 'clubsoccer', 'football', 'roster', 'schedule', 'tickets', 'imdb.com',
    'contact', 'about', 'shopping', 'usnews.com', 'ncaa.com', 'collegefactual.com', 'bigfuture.colllegeboard.org',
    'msche.org', 'prepsportswear.com', 'topdrawersoccer.com', 'jnj.com', 'www.johnsonfinancialgroup.com'
}

def extract_url(href: str) -> Optional[str]:
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('url', [None])[0]



def google_search(query: str) -> List[str]:
    search_url = f"https://www.google.com/search?q={query}"
    response = send_request_with_rate_limit_handling(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    selected_hrefs = []
    seen_urls = set()
    anchors = soup.find_all('a', href=True)

    for item in anchors:
        href = item['href']
        if not href.startswith('/url?'):
            continue

        extracted_url = extract_url(href)
        if not extracted_url or not extracted_url.startswith('http'):
            continue

        if any(substring in extracted_url for substring in filter_substrings):
            print(f"Filtering out URL: '{extracted_url}'")
            continue

        if extracted_url not in seen_urls:
            selected_hrefs.append(extracted_url)
            seen_urls.add(extracted_url)


    print(f"Selected {len(selected_hrefs)} search results for: '{query}'")
    for url in selected_hrefs:
        print(f"\t{url}")

    return selected_hrefs
