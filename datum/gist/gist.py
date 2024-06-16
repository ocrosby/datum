import os
import requests
import json

from dotenv import load_dotenv

# Your GitHub token
token = 'your_github_token'

# The API URL for creating gists
url = 'https://api.github.com/gists'

# The headers for the API request
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',
}

# The data for the gist
data = {
    'public': True,
    'files': {
        'test.txt': {
            'content': 'Hello, world!'
        }
    }
}

# Send the API request
response = requests.post(url, headers=headers, data=json.dumps(data))

# Print the URL of the created gist
print(response.json()['html_url'])
