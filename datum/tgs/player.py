"""
This module contains functions for retrieving player data from the Total Global Sports API.
"""

import requests

BASE_URL = "https://public.totalglobalsports.com/api/player"


def get_all_countries() -> list[tuple]:
    """
    Returns a list of tuples containing the country ID, country name, and country code.
    """
    url = f"{BASE_URL}/get-all-countries"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    records = []
    for item in data["data"]:
        records.append((item["countryID"],
                        item["country"],
                        item["countrycode"]))

    return records


def get_all_states() -> list[tuple]:
    """
    Returns a list of tuples containing the state ID, region ID, country ID, state code, state name, state image, and time zone ID.
    """
    url = f"{BASE_URL}/get-all-states"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    records = []
    for item in data["data"]:
        records.append((item["stateID"],
                        item["regionID"],
                        item["countryID"],
                        item["stateCode"],
                        item["stateName"],
                        item["stateImage"],
                        item["timeZoneID"]))

    return records


def get_college_division_list() -> list[tuple]:
    """
    Returns a list of tuples containing the college division name and abbreviation.
    """
    url = f"{BASE_URL}/get-college-division-list"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    records = []
    for item in data["data"]:
        records.append((item["collegeDivisionID"],
                        item["collegeDivisionName"]))

    sorted_records = sorted(records, key=lambda x: x[1])

    return sorted_records


def get_college_conference_list() -> list[tuple]:
    """
    Returns a list of tuples containing the college conference ID, division ID, and conference name.
    """
    url = f"{BASE_URL}/get-college-conference-list"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    records = []
    for item in data["data"]:
        records.append((item["collegeconferenceID"],
                        item["collegedivisionID"],
                        item["conferencename"]))

    sorted_records = sorted(records, key=lambda x: (x[1], x[2]))

    return sorted_records


if __name__ == "__main__":
    countries = get_all_countries()
    states = get_all_states()
    divisions = get_college_division_list()
    conferences = get_college_conference_list()

    print("\nCountries")
    for country in countries:
        print(country)

    print("\nStates")
    for state in states:
        print(state)

    print("\nDivisions")
    for division in divisions:
        print(division)

    print("\nConferences")
    for conference in conferences:
        print(conference)
