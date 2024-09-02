import os
import csv

from threading import Lock
from typing import List
from index_processor.school_record import SchoolRecord, create_school_record_from_row

file_lock = Lock()

def read_index(file_path: str) -> List[SchoolRecord]:
    school_records = []
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                school_record = create_school_record_from_row(row)
                school_records.append(school_record)
            except ValueError as e:
                print(f"Error creating school record: {e}\nRow: {row}")
    return school_records


def delete_files(file_paths: list):
    for file_path in file_paths:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")


def update_index_file(file_path: str, record: SchoolRecord):
    updated_records = []
    with file_lock:
        with open(file_path, mode='r') as f:
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
        with open(file_path, mode='w', newline='') as f:
            fieldnames = ['Short Name', 'Long Name', 'Vendor', 'WOSO URL', 'MOSO URL']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_records)

def append_to_text_file(file_path: str, data: str):
    with file_lock:
        with open(file_path, 'a') as f:
            f.write(f"{data}\n")


def append_to_csv_file(file_path: str, data: list):
    with file_lock:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)