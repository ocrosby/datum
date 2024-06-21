from datetime import datetime

import requests

from datum.tgs import player

BASE_URL = "https://public.totalglobalsports.com/api/Event"


def get_by_id(event_id: int) -> dict:
    """
    Returns the event data for the specified event ID.

    :param event_id: The event ID (9 for girls ECNL).
    :return: The event data.
    """
    url = f"{BASE_URL}/get-event-details-by-eventID/{event_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    try:
        json_data = response.json()
    except requests.exceptions.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"\nResponse content: {response.content}")
        return {}

    data = json_data.get("data")
    return data


def get_colleges_attending(event_id: int) -> list[tuple[dict, list]]:
    """
    Returns a list of colleges attending the specified event ID.
    """
    url = f"{BASE_URL}/get-colleges-attending-list-with-coaches-by-event/{event_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    json_data = response.json()
    data = json_data.get("data")

    results = []
    for item in data:
        college_info = item["collegeInfo"]
        coach_list = item["coachList"]

        # Combine the first and last names of the coaches
        for current_coach in coach_list:
            current_coach["name"] = f"{current_coach['firstname']} {current_coach['lastname']}"

        results.append((college_info, coach_list))

    return results


def get_clubs(org_id: int) -> list[tuple]:
    """
    Returns a list of clubs for the specified organization ID.
    """
    url = f"{BASE_URL}/get-club-list-by-organizationID/{org_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    json_data = response.json()

    data = json_data.get("data")

    records = []
    for item in data:
        records.append((item["clubID"],
                        item["clubName"]))

    return records


def get_clubs_with_commitment_counts() -> list[tuple]:
    """
    Returns a list of clubs with the number of commitments.
    """
    url = f"{BASE_URL}/get-all-tgs-club-list-with-committed-counts"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    json_data = response.json()

    data = json_data.get("data")

    records = []
    for record in data:
        records.append((record["clubID"],
                        record["clubName"],
                        record["nationalRank"],
                        record["stateRank"],
                        record["city"],
                        record["zip"],
                        record["stateID"],
                        record["stateCode"],
                        record["girlsCommitted"],
                        record["boysCommitted"],
                        record["totalCommitted"],
                        record["clubLogo"]))

    return records

def _translate_date(date_string: str) -> str:
    """
    Translates the date string to a more readable format.
    """
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    return date.strftime("%B %d, %Y")


def process_event(event_id: int):
    event = get_by_id(event_id)

    print("-" * 80)
    print(event["name"])
    print(event["location"])

    alpha_date = _translate_date(event["eventStartDate"])
    omega_date = _translate_date(event["eventEndDate"])

    print(f"{alpha_date} - {omega_date}")

    print("\nColleges Attending")
    colleges_attending = get_colleges_attending(event_id)
    for college, coaches in colleges_attending:
        print(college["collegename"])
        for coach in coaches:
            print(f"\t{coach['name']}, {coach['email']}, {coach['phone']}")


def process_events(event_ids: list[int]):
    for event_id in event_ids:
        process_event(event_id)


if __name__ == "__main__":
    identifiers = [
        3009,
        3010,
        2992,
        3016,
        3028,
        3030,
        3031,
        3033,
        3035,
        3036,
        3064
    ]

    divisions = player.get_college_division_list()
    conferences = player.get_college_conference_list()
    states = player.get_all_states()
    countries = player.get_all_countries()

    process_events(identifiers)

    # event = get_by_id(3064)
    # colleges_attending = get_colleges_attending(3064)
    #
    # print(event["name"])
    # print(event["location"])
    #
    # startDateString = event["eventStartDate"]
    # endDateString = event["eventEndDate"]
    #
    # startDate = datetime.strptime(startDateString, "%Y-%m-%dT%H:%M:%S")
    # endDate = datetime.strptime(endDateString, "%Y-%m-%dT%H:%M:%S")
    #
    # readableStartDate = startDate.strftime("%B %d, %Y")
    # readableEndDate = endDate.strftime("%B %d, %Y")
    #
    # print(f"{readableStartDate} - {readableEndDate}")
    #
    # print("\nColleges Attending")
    # for college, coaches in colleges_attending:
    #     print(college["collegename"])
    #     for coach in coaches:
    #         print(f"  {coach['name']}, {coach['email']}, {coach['phone']}")


