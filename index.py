import os
import csv

from index_processor.file_operations import read_index, update_index_file, append_to_text_file, append_to_csv_file, delete_files
from index_processor.search import google_search
from index_processor.vendor_detection import determine_vendor
from index_processor.school_record import SchoolRecord
from index_processor.constants import HEADERS


INDEX_FILE = "data/index.csv"
PROCESSED_FILE = "processed_records.csv"
FAILED_REQUESTS_FILE = "failed_requests.txt"
UNRECOGNIZED_VENDORS_FILE = "unrecognized_vendors.txt"
BLACKLIST_FILE = "blacklist.txt"

def load_processed_records(file_path: str) -> set:
    processed_records = set()
    if os.path.isfile(file_path):
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                processed_records.add(row[0])  # Assuming the first column is the short name
    return processed_records


def load_blacklist(file_path: str) -> set:
    blacklist = set()
    if os.path.isfile(file_path):
        with open(file_path, mode='r') as file:
            for line in file:
                blacklist.add(line.strip())
    return blacklist

def process_record(record: SchoolRecord, processed_records: set, blacklist: set):
    if record.short_name in processed_records:
        print(f"Skipping already processed record: {record.long_name}")
        return

    print(f"Processing record: {record.long_name}")

    search_query = f"{record.long_name} Soccer"
    search_results = google_search(search_query)

    if search_results:
        print(f"Found {len(search_results)} search results for: '{search_query}'")

        for url in search_results:
            if url in blacklist:
                print(f"Skipping blacklisted URL: {url}")
                continue

            if 'womens' in url and 'soccer' in url:
                record.womens_soccer_url = url
            elif 'mens' in url and 'soccer' in url:
                record.mens_soccer_url = url

            if not record.has_vendor():
                record.vendor = determine_vendor(url, HEADERS)

        if record.vendor is None or record.vendor == '':
            record.vendor = 'None'

        if record.mens_soccer_url is None or record.mens_soccer_url == '':
            record.mens_soccer_url = 'None'

        if record.womens_soccer_url is None or record.womens_soccer_url == '':
            record.womens_soccer_url = 'None'

        print(repr(record))
        # update_index_file(INDEX_FILE, record)
        append_to_csv_file(PROCESSED_FILE, [record.short_name, record.long_name, record.vendor, record.womens_soccer_url, record.mens_soccer_url])
    else:
        append_to_text_file('no_search_results.txt', search_query)
        print(f"No search results found for: '{search_query}'")

def main():
    records = read_index(INDEX_FILE)
    processed_records = load_processed_records(PROCESSED_FILE)
    blacklist = load_blacklist(BLACKLIST_FILE)
    unprocessed_records = [record for record in records if record.is_unprocessed()]

    print(f"Read {len(records)} records from {INDEX_FILE}")
    print(f"Found {len(unprocessed_records)} unprocessed records")

    delete_files([FAILED_REQUESTS_FILE, UNRECOGNIZED_VENDORS_FILE])

    if not os.path.isfile(PROCESSED_FILE):
        append_to_text_file(PROCESSED_FILE, "Short Name,Long Name,Vendor,WOSO URL,MOSO URL")

    for record in unprocessed_records:
        process_record(record, processed_records, blacklist)

if __name__ == "__main__":
    main()