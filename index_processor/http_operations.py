import time
from sys import excepthook
from http.client import RemoteDisconnected

import requests

def send_request_with_rate_limit_handling(url: str, headers: dict, max_retries: int = 5, retry_delay: int = 60) -> requests.Response:
    retries = 0
    current_delay = retry_delay
    while retries < max_retries:
        try:
            print(f"Sending request to {url}...")
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after else 60
                print(f"Rate limited. Waiting {wait_time} seconds before retrying.")
                time.sleep(wait_time)
            else:
                return response
        except (requests.exceptions.ConnectionError, RemoteDisconnected) as e:
            print(f"Connection error: {e}. Retrying in {current_delay} seconds...")
            time.sleep(current_delay)
            retries += 1
            current_delay *= 2

    raise requests.exceptions.ConnectionError(f"Failed to connect to {url} after {max_retries} retries.")
