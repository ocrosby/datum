from idlelib.pyparse import trans

import requests
import csv
import io

from urllib.parse import urlparse, urlunparse
from typing import Optional

from bs4 import BeautifulSoup

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


def read_sidearm_roster(url: str) -> list[Player]:
    # Since this is a Sidearm vendor, we will process by appending '/roster' to the URL
    # then use BeautifulSoup to parse the HTML content
    parsed_url = urlparse(url)
    new_path = parsed_url.path.rstrip('/') + '/roster'
    roster_url = urlunparse(parsed_url._replace(path=new_path))

    response = requests.get(roster_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    players = []

    list_items = soup.find_all('li', class_='sidearm-roster-player')
    for list_item in list_items:
        player = Player()

        name_div = list_item.find('div', class_='sidearm-roster-player-name')
        player.name = name_div.find('h3').text.strip()
        player.number = name_div.find('span', class_='sidearm-roster-player-jersey-number').text.strip()


        position_span = list_item.find('span', class_='sidearm-roster-player-position-long-short')
        if position_span is None:
            player.position = None
        else:
            player.position = position_span.text.strip()

        player.year = list_item.find('span', class_='sidearm-roster-player-academic-year').text

        players.append(player)

    return players

def read_wmt_roster(url: str):
    pass

def read_prestosports_roster(url: str):
    pass

if __name__ == "__main__":
    programs = read_soccer_programs()

    data = []
    for program in programs:
        if program.has_vendor():
            if program.vendor == 'Sidearm':
                # Process Sidearm vendor
                if program.has_womens_soccer_url():
                    current_program_roster = read_sidearm_roster(program.womens_soccer_url)
                    data.append((program, current_program_roster))
            else:
                print(f"Unsupported vendor: {program.vendor}")

    # Count the total number of players
    total_players = 0
    for program, roster in data:
        total_players += len(roster)

    print(f"Total players: {total_players}")
