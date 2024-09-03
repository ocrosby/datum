from idlelib.pyparse import trans

import requests
import csv
import io

from urllib.parse import urlparse, urlunparse
from typing import Optional

from bs4 import BeautifulSoup

from index_processor.http_operations import send_request_with_rate_limit_handling

# URL of the public gist containing the CSV file
gist_url = 'https://gist.githubusercontent.com/ocrosby/6c399ae3905c6ef5bd5b6518e42c53e0/raw/soccer_programs.csv'

class Program:
    short_name: str
    long_name: str
    vendor: str
    womens_soccer_url: str
    mens_soccer_url: str

    def has_vendor(self) -> bool:
        return self.vendor is not None and len(self.vendor) > 0

    def has_womens_soccer_url(self) -> bool:
        return self.womens_soccer_url is not None and len(self.womens_soccer_url) > 0

    def has_mens_soccer_url(self) -> bool:
        return self.mens_soccer_url is not None and len(self.mens_soccer_url) > 0


class Player:
    name: str
    number: str
    position: str
    year: str



def translate_value(value: str) -> Optional[str]:
    if value == None:
        return None

    value = value.strip()

    if len(value) == 0:
        return None

    if value == 'None':
        return None

    return value


def read_soccer_programs() -> list[Program]:
    response = requests.get(gist_url)
    response.raise_for_status()

    programs = []
    csv_reader = csv.reader(io.StringIO(response.text))

    # Read the header row
    _ = next(csv_reader)

    # Read the data
    for row in csv_reader:
        short_name = translate_value(row[0])
        long_name = translate_value(row[1])
        vendor = translate_value(row[2])
        womens_soccer_url = translate_value(row[3])
        mens_soccer_url = translate_value(row[4])

        program = Program()
        program.short_name = short_name
        program.long_name = long_name
        program.vendor = vendor
        program.womens_soccer_url = womens_soccer_url
        program.mens_soccer_url = mens_soccer_url

        programs.append(program)

    return programs


class RosterRetrievalException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UnsupportedVendorError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def read_sidearm_roster(url: str) -> list[Player]:
    # Since this is a Sidearm vendor, we will process by appending '/roster' to the URL
    # then use BeautifulSoup to parse the HTML content
    parsed_url = urlparse(url)
    new_path = parsed_url.path.rstrip('/') + '/roster'
    roster_url = urlunparse(parsed_url._replace(path=new_path))

    # Ensure roster_url is a string
    if not isinstance(roster_url, str):
        roster_url = roster_url.decode('utf-8')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

    response = send_request_with_rate_limit_handling(roster_url, headers=headers)

    if response.status_code != 200:
        raise RosterRetrievalException(f"Failed to fetch roster URL: {roster_url}")

    soup = BeautifulSoup(response.text, 'html.parser')

    players = []

    list_items = soup.find_all('li', class_='sidearm-roster-player')
    for list_item in list_items:
        player = Player()

        name_div = list_item.find('div', class_='sidearm-roster-player-name')

        if name_div is None:
            continue

        name_heading = name_div.find('h3')
        number_span = name_div.find('span', class_='sidearm-roster-player-jersey-number')

        if name_div is None:
            continue

        if name_heading is None:
            continue

        player.name = name_heading.text.strip()

        if number_span is None:
            player.number = None
        else:
            player.number = number_span.text.strip()

        position_span = list_item.find('span', class_='sidearm-roster-player-position-long-short')
        if position_span is None:
            player.position = None
        else:
            player.position = position_span.text.strip()

        year_span = list_item.find('span', class_='sidearm-roster-player-academic-year')
        if year_span is None:
            player.year = None
        else:
            player.year = list_item.find('span', class_='sidearm-roster-player-academic-year').text

        players.append(player)

    return players

def read_wmt_roster(url: str):
    # Since this is a Sidearm vendor, we will process by appending '/roster' to the URL
    # then use BeautifulSoup to parse the HTML content
    parsed_url = urlparse(url)
    new_path = parsed_url.path.rstrip('/') + '/roster'
    roster_url = urlunparse(parsed_url._replace(path=new_path))

    # Ensure roster_url is a string
    if not isinstance(roster_url, str):
        roster_url = roster_url.decode('utf-8')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

    response = send_request_with_rate_limit_handling(roster_url, headers=headers)

    if response.status_code != 200:
        raise RosterRetrievalException(f"Failed to fetch roster URL: {roster_url}")

    soup = BeautifulSoup(response.text, 'html.parser')

    players = []

    rows = soup.find_all('tr')
    for row in rows:
        player = Player()
        columns = row.find_all('td')

        if len(columns) < 5:
            continue

        player.number = columns[0].text.strip()
        player.name = columns[1].text.strip()
        player.position = columns[2].text.strip()
        player.year = columns[4].text.strip()

        players.append(player)

    return players


def read_prestosports_roster(url: str):
    pass

if __name__ == "__main__":
    programs = read_soccer_programs()

    program_rosters = []
    for program in programs:
        try:
            if not program.has_vendor():
                continue

            if program.vendor not in ['Sidearm', 'WMT']:
                raise UnsupportedVendorError(f"Unsupported vendor: {program.vendor}")

            if program.vendor == 'Sidearm' and program.has_womens_soccer_url():
                try:
                    current_program_roster = read_sidearm_roster(program.womens_soccer_url)
                    program_rosters.append((program, current_program_roster))
                except RosterRetrievalException as e:
                    print(e)
            elif program.vendor == 'WMT' and program.has_womens_soccer_url():
                try:
                    current_program_roster = read_wmt_roster(program.womens_soccer_url)
                    program_rosters.append((program, current_program_roster))
                except RosterRetrievalException as e:
                    print(e)
        except UnsupportedVendorError as e:
            print(e)

    # Count the total number of players
    total_players = 0
    for program, roster in program_rosters:
        total_players += len(roster)

    print(f"Total players: {total_players}")
