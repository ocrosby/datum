"""
This script reads the index file and processes the records. It can be used to determine which records have been processed and which have not.
"""

import csv
import time
import os.path
from re import findall
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

import requests

from typing import Optional

from bs4 import BeautifulSoup

INDEX_FILE = "data/index.csv"
WMT_URL = "https://wmt.digital"
SIDEARM_URL = "https://sidearmsports.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

class SchoolRecord:
    """
    Represents a record in the index file. Each record has a short name, long name
    """
    short_name: str
    long_name: str
    vendor: str
    womens_soccer_url: str
    mens_soccer_url: str

    def __str__(self):
        return self.long_name

    def __repr__(self):
        return f"SchoolRecord(short_name='{self.short_name}', long_name='{self.long_name}', vendor='{self.vendor}', womens_soccer_url='{self.womens_soccer_url}', mens_soccer_url='{self.mens_soccer_url}')"

    def has_womens_soccer_url(self) -> bool:
        """
        A record is considered to have a women's soccer URL if the field is not empty and not None
        """
        if self.womens_soccer_url is None:
            return False

        if self.womens_soccer_url.strip() == "":
            return False

        return True

    def has_mens_soccer_url(self) -> bool:
        """
        A record is considered to have men's soccer URL if the field is not empty and not None
        """
        if self.mens_soccer_url is None:
            return False

        if self.mens_soccer_url.strip() == "":
            return False

        return True

    def has_soccer_urls(self) -> bool:
        """
        A record is considered to have soccer URLs if it has either a non-trivial men's or women's soccer url.
        """
        return self.has_womens_soccer_url() or self.has_mens_soccer_url()

    def has_vendor(self) -> bool:
        """
        A record is considered to have a vendor if the vendor field is not empty
        """
        if self.vendor is None:
            return False

        if self.vendor.strip() == "":
            return False

        return True

    def is_processed(self) -> bool:
        """
        A record is considered processed if it has soccer URLs and a vendor
        """
        return self.has_soccer_urls() and self.has_vendor()

    def is_unprocessed(self) -> bool:
        """
        A record is considered unprocessed if it does not have soccer URLs or a vendor
        """
        return not self.is_processed()


def read_nullable_field(row, field_name) -> Optional[str]:
    value = row[field_name]
    if value == "None":
        return None

    return value

def create_school_record_from_row(row) -> SchoolRecord:
    if row is None:
        raise ValueError("Row cannot be None")

    record = SchoolRecord()
    record.short_name = row['Short Name']
    record.long_name = row['Long Name']
    record.vendor = read_nullable_field(row, 'Vendor')
    record.womens_soccer_url = read_nullable_field(row, 'WOSO URL')
    record.mens_soccer_url = read_nullable_field(row, 'MOSO URL')

    return record


def read_index() -> list[SchoolRecord]:
    school_records = []

    with open(INDEX_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                school_record = create_school_record_from_row(row)
                school_records.append(school_record)
            except ValueError as e:
                print(f"Error creating school record: {e}\nRow: {row}")

    return school_records


def get_processed_records(records: list[SchoolRecord]) -> list[SchoolRecord]:
    processed_records = []

    for record in records:
        if record.is_processed():
            processed_records.append(record)

    return processed_records

def get_unprocessed_records(records: list[SchoolRecord]) -> list[SchoolRecord]:
    unprocessed_records = []

    for record in records:
        if record.is_processed():
            continue

        if record.vendor == '':
            record.vendor = None

        if record.mens_soccer_url == '':
            record.mens_soccer_url = None

        if record.womens_soccer_url == '':
            record.womens_soccer_url = None

        unprocessed_records.append(record)

    return unprocessed_records

def extract_url(href: str) -> Optional[str]:
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return None

# Define a set of substrings to filter out
filter_substrings = {
    'google.com', 'facebook.com', 'twitter.com', 'instagram.com', 'wikipedia.org',
    'ncsasports.org', 'hudl.com', 'youtube.com', 'coaches', 'sportsrecruits.com',
    'reddit.com', 'staff-directory', 'basketball', 'baseball', 'softball', 'volleyball', 'club-soccer', 'clubsoccer', 'football', 'roster', 'schedule', 'tickets'
}

def send_request_with_rate_limit_handling(url: str, headers: dict) -> requests.Response:
    while True:
        response = requests.get(url, headers)

        if response.status_code == 429:  # Rate limited
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                print(f"Rate limited. Waiting {wait_time} seconds before retrying.")
                time.sleep(wait_time)
            else:
                print("Rate limited. Waiting 10 seconds before retrying.")
                time.sleep(60)
        else:
            return response


def google_search(query: str) -> list[str]:
    search_url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = send_request_with_rate_limit_handling(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    selected_hrefs = []

    # Google search results are typically in <a> tags with "href" attributes
    anchors = soup.find_all('a', href=True)

    interesting_hrefs = []
    for item in anchors:
        href = item['href']

        if not href.startswith('/url?'):
            continue

        extracted_url = extract_url(href)

        if extracted_url is None:
            continue

        if not extracted_url.startswith('http'):
            continue

        for substring in filter_substrings:
            if substring in extracted_url:
                print(f"Filtering out URL: '{extracted_url}' because it contains '{substring}'")
                break
        else:
            selected_hrefs.append(extracted_url)

    return selected_hrefs


def is_sidearm_url(url: str) -> bool:
    response = requests.get(url)
    if response.status_code != 200:
        return False

    return SIDEARM_URL in response.text

def is_wmt_url(url: str) -> bool:
    response = requests.get(url)
    if response.status_code != 200:
        return False

    return WMT_URL in response.text

# Create a global lock object
file_lock = Lock()

def append_to_file(file_path: str, data: str):
    with file_lock:
        with open(file_path, 'a') as f:
            f.write(f"{data}\n")


def determine_vendor(url: str, headers: dict) -> Optional[str]:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if 'sidearmsports.com' in response.text:
            return "Sidearm"
        elif WMT_URL in response.text:
            return "WMT"
        elif 'prestosports.com' in response.text:
            return "PrestoSports"
        else:
            append_to_file('unrecognized_vendors.txt', url)
    else:
        append_to_file('failed_requests.txt', url)

    return None

def is_url_womens_soccer(url: str) -> bool:
    """
    Determines if a URL is a women's soccer URL
    """
    if 'womens' in url:
        if "soccer" in url:
            return True
    elif 'woso' in url:
        return True
    elif 'wsoc' in url:
        return True

    return False

def is_url_mens_soccer(url: str) -> bool:
    """
    Determines if a URL is a men's soccer URL
    """
    if is_url_womens_soccer(url):
        return False

    if 'mens' in url:
        if "soccer" in url:
            return True
    elif 'mso' in url:
        return True
    elif 'msoc' in url:
        return True

    return False


def update_index_file(record: SchoolRecord):
    index_file = 'new_index.csv'
    updated_records = []

    with file_lock:
        with open(index_file, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Short Name'] == record.short_name and row['Long Name'] == record.long_name:
                    if not row['Vendor']:
                        row['Vendor'] = record.vendor
                    if not row['WOSO URL']:
                        row['WOSO URL'] = record.womens_soccer_url
                    if not row['MOSO URL']:
                        row['MOSO URL'] = record.mens_soccer_url
                updated_records.append(row)

    with file_lock:
        with open(index_file, mode='w', newline='') as f:
            fieldnames = ['Short Name', 'Long Name', 'Vendor', 'WOSO URL', 'MOSO URL']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_records)


def process_record(record: SchoolRecord):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    print(f"Processing record: {record.long_name}")

    search_query = f"{record.long_name} Soccer"
    search_results = google_search(search_query)

    if len(search_results) > 0:
        print(f"Found {len(search_results)} search results for: '{search_query}'")

        for url in search_results:
            found_womens_soccer_url = is_url_womens_soccer(url)
            found_mens_soccer_url = is_url_mens_soccer(url)

            if not found_womens_soccer_url and not found_mens_soccer_url:
                print(f"Unrecognized URL: {url}")
                append_to_file("unrecognized_urls.txt", url)
                continue
            else:
                print(f"Recognized URL: {url}")

            if found_womens_soccer_url:
                record.womens_soccer_url = url

            if found_mens_soccer_url:
                record.mens_soccer_url = url

            if not record.has_vendor():
                record.vendor = determine_vendor(url, headers)

        print(repr(record))

        update_index_file(record)
        append_to_file('processed_records.csv', f"{record.short_name},{record.long_name},{record.vendor},{record.womens_soccer_url},{record.mens_soccer_url}")
    else:
        append_to_file('no_search_results.txt', search_query)
        print(f"No search results found for: '{search_query}'")


def main():
    records = read_index()
    processed_records = get_processed_records(records)
    unprocessed_records = get_unprocessed_records(records)

    print(f"Read {len(records)} records from {INDEX_FILE}")
    print(f"Found {len(processed_records)} processed records")
    print(f"Found {len(unprocessed_records)} unprocessed records")

    if os.path.isfile('processed_records.txt'):
        os.remove('processed_records.txt')

    if os.path.isfile('processed_records.csv'):
        os.remove('processed_records.csv')

    append_to_file('processed_records.csv', "Short Name,Long Name,Vendor,WOSO URL,MOSO URL")

    if os.path.isfile('unrecognized_urls.txt'):
        os.remove('unrecognized_urls.txt')

    if os.path.isfile('unrecognized_vendors.txt'):
        os.remove('unrecognized_vendors.txt')

    if os.path.isfile('failed_requests.txt'):
        os.remove('failed_requests.txt')

    if os.path.isfile('no_search_results.txt'):
        os.remove('no_search_results.txt')

    print("Processing unprocessed records")
    for record in unprocessed_records:
        process_record(record)

    # max_threads = 1 # Number of threads to use for processing records
    # with ThreadPoolExecutor(max_workers=max_threads) as executor:
    #     executor.map(process_record, unprocessed_records)

if __name__ == "__main__":
    main()

