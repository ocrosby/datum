from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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
    # Set up headless browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Since this is a Sidearm vendor, we will process by appending '/roster' to the URL
    # then use BeautifulSoup to parse the HTML content
    parsed_url = urlparse(url)
    new_path = parsed_url.path.rstrip('/') + '/roster'
    roster_url = urlunparse(parsed_url._replace(path=new_path))

    # Ensure roster_url is a string
    if not isinstance(roster_url, str):
        roster_url = roster_url.decode('utf-8')

    driver.get(roster_url)
    page_source = driver.page_source
    driver.quit()

    # Write the text content of the response to a file
    with open('roster.html', 'w') as file:
        file.write(page_source)

    soup = BeautifulSoup(page_source, 'html.parser')

    players = []

    # .sidearm-roster-templates-container , .flex-align-center
    sidearm_roster_templates_container = soup.find('div', class_='sidearm-roster-templates-container')
    s_person_cards = soup.find_all('div', class_=['s-person-card', 'dataTable'])
    roster_list = soup.select('ul#roster-players')

    if len(s_person_cards) > 0:
        # Handle this case for SideArm sites that use the s-person-card class
        for card in s_person_cards:
            player = Player()

            # Extract player name
            name_tag = card.find('h3')
            if name_tag:
                player.name = name_tag.text.strip()

            # Extract jersey number
            number_tag = card.find('span', class_='s-stamp__text')
            if number_tag:
                player.number = number_tag.text.strip()
                if 'Jersey Number' in player.number:
                    player.number = player.number.replace('Jersey Number', '')
                    player.number = player.number.strip()

            # Extract player position
            bio_stats_items = card.find_all('span', class_='s-person-details__bio-stats-item')

            if len(bio_stats_items) < 2:
                continue

            player.position = bio_stats_items[0].text.replace('Position', '').strip()
            player.year = bio_stats_items[1].text.replace('Academic Year', '').strip()

            players.append(player)
    elif roster_list is not None:
        # Handle this case for SideArm sites that use the sidearm-roster-list class
        list_items = roster_list[0].find_all('li', class_='sidearm-roster-list-item-link')
        for list_item in list_items:
            player = Player()

            name_div = list_item.find('div', class_='sidearm-roster-list-item-name')

            if name_div is None:
                continue

            player.name = name_div.text.strip()


            if name_div is None:
                continue

            number_div = name_div.find('div', class_='sidearm-roster-list-item-photo-number')
            if number_div is None:
                continue

            player.number = number_div.text.strip()

            year_span = list_item.find('span', class_='sidearm-roster-list-item-year')
            if year_span is None:
                continue

            player.year = year_span.text.strip()


            position_span = list_item.find('span', class_='sidearm-roster-list-item-position')
            if position_span is None:
                continue

            player.position = position_span.text.strip()

            players.append(player)
    elif sidearm_roster_templates_container is not None:
        # Handle this case for SideArm sites that use the sidearm-table class
        sidearm_table = sidearm_roster_templates_container.find('table', class_='sidearm-table-grid-template-1-breakdown-large')
        rows = sidearm_table.find_all('tr')
        for row in rows:
            player = Player()

            columns = row.find_all('td')
            if len(columns) < 7:
                continue

            player.number = columns[0].text.strip()
            player.name = columns[2].text.strip()
            player.position = columns[6].text.strip()
            player.year = columns[4].text.strip()

            players.append(player)
    else:
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
                    if len(current_program_roster) == 0:
                        print(f"No roster found for {program.long_name}")
                        continue

                    for player in current_program_roster:
                        print(f"{program.long_name}, #{player.number}: {player.name} - {player.position} - {player.year}")
                except RosterRetrievalException as e:
                    print(e)
            elif program.vendor == 'WMT' and program.has_womens_soccer_url():
                try:
                    current_program_roster = read_wmt_roster(program.womens_soccer_url)
                    if len(current_program_roster) == 0:
                        print(f"No roster found for {program.long_name}")
                        continue

                    for player in current_program_roster:
                        print(f"{program.long_name}, #{player.number}: {player.name} - {player.position} - {player.year}")
                except RosterRetrievalException as e:
                    print(e)
        except UnsupportedVendorError as e:
            print(e)
