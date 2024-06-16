from typing import List, Dict

import requests


class Player:
    def __init__(self):
        self.Name = None
        self.Number = None
        self.Role = None
        self.Team = None

    def __str__(self):
        return f"{self.Name} (#{self.Number}) - {self.Team} {self.Role}"


def get_schools_to_players() -> Dict[str, List[str]]:
    school_to_players = {}

    with open('schools.txt', 'r') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()
            if ':' in line:
                player_name, schools = line.split(':')
                schools = schools.split(',')
                schools = [school.strip() for school in schools]

                for school in schools:
                    if school in school_to_players:
                        school_to_players[school].append(player_name)
                    else:
                        school_to_players[school] = [player_name]

    return school_to_players


def get_json_from_url(url: str):
    response = requests.get(url)

    # Check if the GET request was successful
    if response.status_code != 200:
        raise Exception(f"GET request failed with status code {response.status_code}")

    # Parse the JSON response
    data = response.json()

    return data


def get_nwsl_players() -> List[Player]:
    """
    :return:
    """
    url = "https://nwsl-api-prd-sdp.akamaized.net/v1/nwsl/football/seasons/nwsl::Football_Season::fe17bea0b7234cf7957c7249cb828270/stats/players?locale=en-US&category=general&orderBy=goals&role=all&direction=desc&page=1&pageNumElement=400"
    players = []

    data = get_json_from_url(url)

    for player in data['players']:
        p = Player()
        p.Name = player['mediaFirstName'] + ' ' + player['mediaLastName']
        p.Number = player['bibNumber']
        p.Role = player['roleLabel']
        p.Team = player['team']['mediaShortName']

        players.append(p)

    # Retrieve all the players from the NWSL.

    return players


def write_player_names_to_file(players: List[Player]):
    with open('names.txt', 'w') as file:
        for player in players:
            file.write(player.Name.strip() + '\n')


if __name__ == "__main__":
    print("NWSL PLayers:")

    players = get_nwsl_players()

    write_player_names_to_file(players)

    for player in players:
        print(player)

    schools_to_players = get_schools_to_players()

    print("\nSchools Frequencies:")
    # Display a list of schools and the count of players who attended each school
    for school, players in schools_to_players.items():
        print(f"{school}: {len(players)}")

    # At this point I have a list of all NWSL players.

    # How can I determine where these players went to college?


    # Step 1: Gather the Data
    # You need data on NWSL players and their respective college programs.
    # This could include names of players, the colleges they attended,
    # and perhaps years of attendance

