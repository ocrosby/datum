import csv
import os

INDEX_FILE = "data/index.csv"
PROCESSED_FILE = "processed_records.csv"

def load_processed_records(file_path: str) -> dict:
    processed_records = {}
    if os.path.isfile(file_path):
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = (row['Short Name'], row['Long Name'])
                processed_records[key] = row
    return processed_records

def update_index_file(index_file: str, processed_records: dict):
    updated_records = []
    with open(index_file, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['Short Name'], row['Long Name'])
            if key in processed_records:
                processed_record = processed_records[key]
                if not row['Vendor']:
                    row['Vendor'] = processed_record['Vendor']
                if not row['WOSO URL']:
                    row['WOSO URL'] = processed_record['WOSO URL']
                if not row['MOSO URL']:
                    row['MOSO URL'] = processed_record['MOSO URL']
            updated_records.append(row)

    with open(index_file, mode='w', newline='') as f:
        fieldnames = ['Short Name', 'Long Name', 'Vendor', 'WOSO URL', 'MOSO URL']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_records)

def main():
    processed_records = load_processed_records(PROCESSED_FILE)
    update_index_file(INDEX_FILE, processed_records)

if __name__ == "__main__":
    main()
