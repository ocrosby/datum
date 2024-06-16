import os
import csv
import warnings
import requests

from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

from typing import List, Dict

warnings.simplefilter('ignore', category=InsecureRequestWarning)


def get_population_data(university_name: str) -> Dict[str,int]:
    # Format the university name to match the URL structure
    university_name = university_name.lower().replace(' ', '-')

    # Construct the URL
    url = f"https://www.univstats.com/colleges/{university_name}/student-population/"

    # Send a GET request to the URL
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise Exception(f"GET request for '{university_name}' failed: {e}")

    # Check if the GET request was successful
    if response.status_code != 200:
        raise Exception(f"GET request for '{university_name}' failed with status code {response.status_code}")

    # Parse the HTML response
    soup = BeautifulSoup(response.text, 'html.parser')

    # Use CSS selector to select divs with 'cardwrap' that are direct children of 'scoreboard'
    card_wraps = soup.select('div.scoreboard > div.cardwrap')

    data = {}

    for card in card_wraps:
        title_span = card.find('span', class_='title')
        value_span = card.find('span', class_='value')

        if title_span and value_span:
            key = title_span.text.strip()
            value = int(value_span.text.strip().replace(',', ''))

            data[key] = value

    return data


def read_institutions(filename: str) -> List[str]:
    """
    Read institutions from a file

    :param filename: A string representing the filename
    :return: A list of strings
    """
    with open(filename, 'r') as file:
        results = [line.strip() for line in file]

    return results


if __name__ == "__main__":
    institutions = read_institutions('institutions.txt')

    output_file = "population_data.csv"
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Institution", "Population"])

        for institution in institutions:
            try:
                data = get_population_data(institution)

                if 'Undergraduate' not in data:
                    writer.writerow([institution, "Data not found"])
                else:
                    population = data['Undergraduate']
                    writer.writerow([institution, population])
            except ValueError as e:
                print(e)
            except Exception as e:
                print(e)



