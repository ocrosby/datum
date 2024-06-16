import warnings
from urllib3.exceptions import NotOpenSSLWarning

# Suppress all warnings
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
from urllib.parse import urljoin

NCAA_URL = "https://www.ncaa.com"

individual_statistics = {
    "Select an Individual Statistic": "",
    "Assists Per Game": "/stats/soccer-women/d1/current/individual/57",
    "Game-Winning Goals": "/stats/soccer-women/d1/current/individual/585",
    "Goalie Minutes Played": "/stats/soccer-women/d1/current/individual/582",
    "Goals Against Average": "/stats/soccer-women/d1/current/individual/55",
    "Goals Per Game": "/stats/soccer-women/d1/current/individual/53",
    "Penalty Kicks": "/stats/soccer-women/d1/current/individual/1207",
    "Points Per Game": "/stats/soccer-women/d1/current/individual/52",
    "Red Cards": "/stats/soccer-women/d1/current/individual/550",
    "Save Pct": "/stats/soccer-women/d1/current/individual/423",
    "Saves Per Game": "/stats/soccer-women/d1/current/individual/54",
    "Shot Accuracy": "/stats/soccer-women/d1/current/individual/1202",
    "Shots Per Game": "/stats/soccer-women/d1/current/individual/983",
    "Shots on Goal Per Game": "/stats/soccer-women/d1/current/individual/985",
    "Shutouts": "/stats/soccer-women/d1/current/individual/1175",
    "Total Assists": "/stats/soccer-women/d1/current/individual/580",
    "Total Goals": "/stats/soccer-women/d1/current/individual/579",
    "Total Points": "/stats/soccer-women/d1/current/individual/578",
    "Total Saves": "/stats/soccer-women/d1/current/individual/581",
    "Yellow Cards": "/stats/soccer-women/d1/current/individual/548"
}

team_statistics = {
    "Select a Team Statistic": "",
    "Assists Per Game": "/stats/soccer-women/d1/current/team/94",
    "Corner Kicks Per Game": "/stats/soccer-women/d1/current/team/1176",
    "Fouls Per Game": "/stats/soccer-women/d1/current/team/547",
    "Goals-Against Average": "/stats/soccer-women/d1/current/team/58",
    "Penalty Kicks": "/stats/soccer-women/d1/current/team/1208",
    "Points Per Game": "/stats/soccer-women/d1/current/team/95",
    "Red Cards": "/stats/soccer-women/d1/current/team/551",
    "Save Pct": "/stats/soccer-women/d1/current/team/424",
    "Saves Per Game": "/stats/soccer-women/d1/current/team/93",
    "Scoring Offense": "/stats/soccer-women/d1/current/team/56",
    "Shot Accuracy": "/stats/soccer-women/d1/current/team/1203",
    "Shots Per Game": "/stats/soccer-women/d1/current/team/984",
    "Shots on Goal Per Game": "/stats/soccer-women/d1/current/team/986",
    "Shutout Percentage": "/stats/soccer-women/d1/current/team/59",
    "Total Assists": "/stats/soccer-women/d1/current/team/910",
    "Total Goals": "/stats/soccer-women/d1/current/team/914",
    "Total Points": "/stats/soccer-women/d1/current/team/915",
    "Won-Lost-Tied Percentage": "/stats/soccer-women/d1/current/team/60",
    "Yellow Cards": "/stats/soccer-women/d1/current/team/549"
}


@dataclass
class IndividualStatistic:
    """Class for keeping track of an individual statistic."""
    name: str
    rank: int
    player: str
    team: str
    year: str
    statistics: dict

    def __init__(self):
        self.name = ""
        self.rank = 0
        self.player = ""
        self.team = ""
        self.year = ""
        self.statistics = {}

    def __str__(self):
        return f"{self.player}: {self.team} {self.year} {self.statistics}"


class IndividualStatisticReader:
    def __init__(self, name: str):
        self.name = name
        self.soup = None
        self.url = urljoin(NCAA_URL, individual_statistics[name])
        self.pages = []
        self.columns = []
        response = requests.get(self.url)
        self.soup = BeautifulSoup(response.text, 'html.parser')

        ul = self.soup.find('ul', class_='stats-pager')
        links = ul.find_all('a')

        for link in links:
            href = link.get('href').strip()
            value = link.text.strip()

            if value.isnumeric():
                self.pages.append((int(value), href))

    def load_page(self, page_index: int):
        driver = webdriver.Chrome()


        for page in self.pages:
            if page[0] == page_index:
                full_url = urljoin(NCAA_URL, page[1])
                driver.get(full_url)

                try:
                    # Wait up to 10 seconds for the elements to become available
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'block-stats__stats-table'))
                    )

                    self.soup = BeautifulSoup(driver.page_source, 'html.parser')

                    # Find the target row
                    target_row = self.soup.find('tr', class_='tablesorter-headerRow')

                    # Find all th elements in the target row
                    headers = target_row.find_all('th')

                    # Extract the captions from the th elements
                    self.columns = [header.find('div').text for header in headers]
                finally:
                    # Close the browser
                    driver.quit()

                break


if __name__ == "__main__":
    reader = IndividualStatisticReader("Assists Per Game")

    print(reader.columns)
    print(reader.pages)

    reader.load_page(1)
