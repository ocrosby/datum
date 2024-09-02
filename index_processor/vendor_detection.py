from typing import Optional
from index_processor.file_operations import append_to_text_file

from index_processor.http_operations import send_request_with_rate_limit_handling

WMT_URL = "https://wmt.digital"
SIDEARM_URL = "https://sidearmsports.com"

def determine_vendor(url: str, headers: dict) -> Optional[str]:
    response = send_request_with_rate_limit_handling(url, headers=headers)
    if response.status_code == 200:
        if 'sidearmsports.com' in response.text:
            return "Sidearm"
        elif WMT_URL in response.text:
            return "WMT"
        elif 'prestosports.com' in response.text:
            return "PrestoSports"
        else:
            append_to_text_file('unrecognized_vendors.txt', url)
    else:
        append_to_text_file('failed_requests.txt', url)

    return None
