from typing import Optional

class SchoolRecord:
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
        return bool(self.womens_soccer_url and self.womens_soccer_url.strip())

    def has_mens_soccer_url(self) -> bool:
        return bool(self.mens_soccer_url and self.mens_soccer_url.strip())

    def has_soccer_urls(self) -> bool:
        return self.has_womens_soccer_url() or self.has_mens_soccer_url()

    def has_vendor(self) -> bool:
        return bool(self.vendor and self.vendor.strip())

    def is_processed(self) -> bool:
        return self.has_soccer_urls() and self.has_vendor()

    def is_unprocessed(self) -> bool:
        return not self.is_processed()

def read_nullable_field(row, field_name) -> Optional[str]:
    value = row[field_name]
    return None if value == "None" else value

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
