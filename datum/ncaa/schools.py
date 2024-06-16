import os
import csv
import requests
import concurrent.futures
import threading

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

SCHOOLS_INDEX_URL = "https://www.ncaa.com/schools-index"

print_lock = threading.Lock()


class School:
    short_name: str
    long_name: str
    ncaa_url: str
    division: str
    city: str
    state: str
    conference: str
    nickname: str
    colors: str
    loadable: bool

    def __init__(self):
        self.short_name = ""
        self.long_name = ""
        self.ncaa_url = ""
        self.division = ""
        self.city = ""
        self.state = ""
        self.conference = ""
        self.nickname = ""
        self.colors = ""
        self.loadable = False

    def __str__(self):
        return f"{self.short_name} ({self.long_name})"

    def is_loadable(self) -> bool:
        return self.loadable

    def normalize(self):
        if len(self.division.strip()) == 0:
            self.division = "Unknown"

        if len(self.conference.strip()) == 0:
            self.conference = "Unknown"

        if len(self.city.strip()) == 0:
            self.city = "Unknown"

        if len(self.state.strip()) == 0:
            self.state = "Unknown"

        if len(self.nickname.strip()) == 0:
            self.nickname = "Unknown"

        if len(self.colors.strip()) == 0:
            self.colors = "Unknown"

    def should_skip(self) -> bool:
        if not self.is_loadable():
            return True

        if self.division in ["", "Unknown"]:
            return True

        if self.conference in ["", "Unknown"]:
            return True

        if self.city in ["", "Unknown"]:
            return True

        if self.state in ["", "Unknown"]:
            return True

        return False


def short_to_long_state(short_state: str) -> str:
    state_map = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "IA": "Iowa",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "ME": "Maine",
        "MD": "Maryland",
        "MA": "Massachusetts",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MS": "Mississippi",
        "MO": "Missouri",
        "MT": "Montana",
        "NE": "Nebraska",
        "NV": "Nevada",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NY": "New York",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VT": "Vermont",
        "VA": "Virginia",
        "WA": "Washington",
        "WV": "West Virginia",
        "WI": "Wisconsin",
        "WY": "Wyoming"
    }

    return state_map.get(short_state, "Unknown")


def generate_page_urls(url: str) -> List[str]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    last_page_link = soup.find('a', string='Last »')

    if last_page_link is None:
        raise ValueError("Could not find the last page link")

    href = last_page_link.get('href').strip()
    page_number = href.split('/')[-1]
    last_page = int(page_number)

    urls = [f"{url}/{i}" for i in range(1, last_page + 1)]

    return urls


def process_url(url: str, max_retries: int) -> List[School]:
    for _ in range(max_retries):
        try:
            with print_lock:
                print(f"Processing {url} ...")

            schools = []

            # For each page extract the school information
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table', class_='responsive-enabled')
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')

                if len(cells) == 0:
                    continue

                current_school = School()

                anchor = cells[1].find('a')

                current_school.short_name = anchor.text.strip()
                current_school.ncaa_url = urljoin('https://www.ncaa.com', anchor.get('href').strip())
                current_school.long_name = cells[2].text.strip()

                if len(current_school.long_name) == 0:
                    current_school.long_name = current_school.short_name

                # Test to see if the url seems valid
                current_school.loadable = requests.head(current_school.ncaa_url).status_code == 200

                schools.append(current_school)

            return schools
        except requests.exceptions.RequestException:
            continue

    return []


def get_schools(urls: List[str], max_retries: int = 3) -> Tuple[List[School], List[str]]:
    schools = []
    failed_urls = []
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(process_url, url, max_retries): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                schools.extend(future.result())
            except Exception as exc:
                with print_lock:
                    print(f"{url} generated an exception: {exc}")
                failed_urls.append(url)

    return schools, failed_urls


def load_school_details(school: School):
    if not school.is_loadable():
        return

    response = requests.get(school.ncaa_url)

    if response.status_code != 200:
        with print_lock:
            print(f"Failed to load {school.short_name} ({school.ncaa_url})")

        return

    soup = BeautifulSoup(response.text, 'html.parser')

    division_location = soup.find('div', class_='division-location')

    if division_location:
        division_location = division_location.text.strip()
        division_location = division_location.replace("\n", "")
        if " - " in division_location:
            try:
                division, location = division_location.split(' - ')

                school.division = division.strip()
                location = location.strip()
                city, state = location.split(',')
                city = city.strip()
                state = state.strip()
                school.city = city
                school.state = state
                school.state = short_to_long_state(school.state)
            except ValueError as err:
                pass

    school_details = soup.find('dl', class_='school-details')
    details = school_details.find_all('dd')

    if len(details) == 3:
        school.conference = details[0].text.strip()
        school.nickname = details[1].text.strip()
        school.colors = details[2].text.strip()

    school.normalize()

def populate_schools(schools: List[School]):
    with ThreadPoolExecutor() as executor:
        # Use map to load all school details in parallel
        executor.map(load_school_details, schools)


if __name__ == "__main__":
    if os.path.isfile("schools.csv"):
        os.remove("schools.csv")

    urls = generate_page_urls(SCHOOLS_INDEX_URL)

    schools, failed_urls = get_schools(urls, max_retries=3)

    if len(failed_urls) > 0:
        print(f"Failed to process {len(failed_urls)} URLs")
        for url in failed_urls:
            print(f"\t{url}")

        exit(1)

    print(f"Found {len(schools)} schools")
    print("Loading school details (please wait) ...")
    populate_schools(schools)
    print("School details loaded.")

    # Sort the schools list by loadable division conference state and then by short_name
    schools = sorted(schools, key=lambda school: (not school.loadable, school.division, school.conference, school.state, school.short_name))

    with open("schools.csv", "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Short Name", "Long Name", "Division", "Conference", "Nickname", "Colors", "City", "State", "Loadable", "NCAA URL"])

        for school in schools:
            # if school.should_skip():
            #     continue

            school.normalize()

            try:
                writer.writerow([school.short_name, school.long_name, school.division, school.conference, school.nickname, school.colors, school.city, school.state, school.loadable, school.ncaa_url])
            except AttributeError as err:
                print(f"Error writing {school.short_name}: {err}")
                print(f"\t{school}")

    print("Done!")
