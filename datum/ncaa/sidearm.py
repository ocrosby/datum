"""
This module contains functions for scraping data from NCAA websites that use the Sidearm Sports platform.
"""

import os
import requests

from bs4 import BeautifulSoup, element
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

SIDEARM_URL = "https://sidearmsports.com"

YEAR_TRANSLATION = {
    "Fr.": "Freshman",
    "So.": "Sophomore",
    "Jr.": "Junior",
    "Sr.": "Senior",
    "Gr.": "Graduate",
    "R-Fr.": "Redshirt Freshman",
    "R-So.": "Redshirt Sophomore",
    "R-Jr.": "Redshirt Junior"
}

@dataclass
class Player:
    name: str
    number: str
    position: str
    height: str
    year: str
    hometown: str
    highschool: str
    social_links: list
    bio_link: str

    def __init__(self):
        self.name = ""
        self.number = ""
        self.position = ""
        self.height = ""
        self.year = ""
        self.hometown = ""
        self.highschool = ""
        self.social_links = []
        self.bio_link = ""

    def __str__(self):
        return f"'{self.name}' ({self.year}) '{self.position}' from '{self.hometown}'"


def is_sidearmsports_page(target_url: str) -> bool:
    resp = requests.get(target_url)

    return SIDEARM_URL in resp.text


def read_player(el: element, prefix: str) -> Player:
    current_player = Player()

    details_element = el.find('div', class_='sidearm-roster-player-details')

    span = details_element.find('span', class_=['sidearm-roster-player-position-long-short', 'hide-on-medium'])
    if span:
        current_player.position = span.text.strip()
    else:
        div = details_element.find('div', class_='sidearm-roster-player-position')
        if div:
            current_player.position = div.find('span').text.strip()

    current_player.height = details_element.find('span', class_='sidearm-roster-player-height').text.strip()
    current_player.number = details_element.find('span', class_='sidearm-roster-player-jersey-number').text.strip()

    name_element = details_element.find('h3')
    if name_element:
        current_player.name = name_element.text.strip()

        relative_link = name_element.find('a').get('href')
        current_player.bio_link = urljoin(prefix, relative_link)

    current_player.social_links = []
    social_elements = details_element.find_all('a', class_='sidearm-roster-player-social-link')
    for social in social_elements:
        current_player.social_links.append(social.get('href'))

    other_element = el.find('div', class_='sidearm-roster-player-other')

    if other_element:
        current_player.year = other_element.find('span', class_='sidearm-roster-player-academic-year').text.strip()
        current_player.hometown = other_element.find('span', class_='sidearm-roster-player-hometown').text.strip()
        current_player.highschool = other_element.find('span', class_='sidearm-roster-player-highschool').text.strip()

    current_player.year = YEAR_TRANSLATION.get(current_player.year, current_player.year)

    return current_player


def get_prefix(target_url: str) -> str:
    parsed_url = urlparse(target_url)
    protocol = parsed_url.scheme
    hostname = parsed_url.netloc

    return f"{protocol}://{hostname}"


def read_players(target_url: str) -> dict:
    if not is_sidearmsports_page(target_url):
        raise ValueError("Not a Sidearm Sports page")

    results = {}
    response = requests.get(target_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    url_prefix = get_prefix(target_url)

    items = soup.find_all('li', class_='sidearm-roster-player')
    for item in items:
        current_player = read_player(item, url_prefix)
        results[current_player.name] = current_player

    return results


if __name__ == "__main__":
    auburn = "https://auburntigers.com/sports/womens-soccer/roster"
    santa_clara = "https://www.santaclarabroncos.com/sports/womens-soccer/roster"

    url = santa_clara

    players = read_players(url)
    for player in players.values():
        print(player)
