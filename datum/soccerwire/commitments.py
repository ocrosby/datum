import os
import csv
import requests


URL = "https://www.soccerwire.com/wp-json/v1/elastic-proxy/soccerwirecom-post-1/_search"


class Player:
    id: str
    gender: str
    name: str
    url: str
    image_url: str
    position: str
    club: str
    league: str
    high_school: str
    rating: str
    year: str
    city: str
    state: str
    commitment: str
    commitment_url: str

    def __str__(self):
        return f"{self.name} ({self.year}) - {self.commitment}"

    def __repr__(self):
        return self.__str__()


def build_payload(gender: str, year: str, size: int = 0):
    return {
        "size": size,
        "post_filter": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "post_type.raw": "players"
                        }
                    },
                    {
                        "term": {
                            "post_status": "publish"
                        }
                    },
                    {
                        "term": {
                            "meta.gender.raw": gender
                        }
                    },
                    {
                        "term": {
                            "meta.graduation_year.raw": year
                        }
                    },
                    {
                        "term": {
                            "meta.is_committed.raw": "1"
                        }
                    }
                ],
                "must_not": []
            }
        },
        "sort": [
            {
                "meta.is_featured.raw": "desc"
            }
        ],
        "query": {
            "function_score": {
                "query": {
                    "multi_match": {
                        "query": "",
                        "operator": "and",
                        "boost": 1,
                        "fuzziness": 1,
                        "prefix_length": 0,
                        "max_expansions": 100
                    }
                }
            }
        },
        "from": 0
    }


def get_number_of_commitments(gender: str, year: str) -> int:
    payload = build_payload(gender, year, 0)
    response = requests.post(URL, json=payload)
    data = response.json()

    return data["hits"]["total"]


# def _get_player_league(player, default="Other"):
#     club = _get_player_club(player, None)
#
#     if club is not None:
#         league = topdrawer_library._get_league(club)
#
#         if league == "Other":
#             league = _get_custom_property(player, "league_title", default)
#             league = _translate_league(league)
#     else:
#         league = _get_custom_property(player, "league_title")
#         league = _translate_league(league)
#
#     return league


def _translate_league(league: str):
    if league == "US Youth Soccer National League P.R.O.":
        return "National League PRO"

    if league == "US Youth Soccer National League":
        return "National League"

    if league == "Elite Clubs National League (ECNL)":
        return "ECNL"

    if league == "ECNL Regional Leagues":
        return "ECRL"

    if league == "Girls Academy":
        return "GA"

    return league


def _translate_commitment(commitment: str):
    if commitment is None:
        return None

    commitment = commitment.strip()
    commitment = commitment.replace(" Women", "")
    commitment = commitment.replace(" Men", "")

    return commitment

def _get_root_property(player, key: str, default = None):
    if player is None:
        return default

    if key is None:
        return default

    key = key.strip()

    if len(key) == 0:
        return default

    if key not in player:
        return default

    return player[key]

def _get_property(player, identifier: str, key: str, default = None):
    if player is None:
        return default

    if key is None:
        return default

    key = key.strip()
    if len(key) == 0:
        return default

    if identifier not in player:
        return default

    if key not in player[identifier]:
        return default

    collection = player[identifier][key]

    if collection is None:
        return default

    if len(collection) < 1:
        return default # This may need to change in the case where there are multiple values.

    item = collection[0]
    if "value" not in item:
        return default

    value = item["value"]
    if value is None:
        if "raw" not in item:
            return default

        value = item["raw"]

        if value is None:
            return default

    value = value.strip()

    if len(value) == 0:
        value = None

    return value


def _get_meta_property(player, key: str, default = None):
    return _get_property(player, "meta", key, default)

def _get_custom_property(player, key: str, default = None):
    if player is None:
        return default

    if key is None:
        return default

    key = key.strip()
    if len(key) == 0:
        return default

    if "custom_fields" not in player:
        return default

    if key not in player["custom_fields"]:
        return default

    value = player["custom_fields"][key]

    if value is None:
        return default

    if type(value) is not str:
        return default

    value = value.strip()

    return value


def _get_player_position(player, default = None):
    if player is None:
        return default

    if "meta" not in player:
        return default

    if "positions" not in player["meta"]:
        return default

    collection = player["meta"]["positions"]

    if collection is None:
        return default

    if len(collection) < 1:
        return default # This may need to change in the case where there are multiple values.

    item = collection[0]
    if "raw" not in item:
        return default

    raw = item["raw"]
    raw = raw.strip()

    if raw == "D":
        return "Defender"

    if raw == "F":
        return "Forward"

    if raw == "GK":
        return "Goalkeeper"

    if raw == "M":
        return "Midfielder"

    if raw is None:
        return default

    if len(raw) == 0:
        return default

    return raw


def _get_player_club(player, default = None):
    club = _get_custom_property(player, "club_title", default)
    # club = config.translate_club_name(club)

    return club


def _get_player_commitment(player, default = None):
    if player is None:
        return default

    commitment = _get_custom_property(player, "college_team", default)
    commitment = _translate_commitment(commitment)

    return commitment


def _get_player_commitment_url(player, default = None):
    if player is None:
        return default

    url = _get_custom_property(player, "college_link", default)

    return url


def _get_player_city(player, default = None):
    city = _get_meta_property(player, "birthplace_city", None)

    if city is None:
        return default

    city = city.strip()
    if len(city) == 0:
        return default

    return city


def _translate_player(player):
    translated_player = Player()
    translated_player.id = _get_root_property(player, "ID", None)
    translated_player.name = _get_root_property(player, "post_title", None)
    translated_player.url = _get_root_property(player, "permalink", None)
    translated_player.image_url = _get_meta_property(player, "image", None)
    translated_player.position = _get_player_position(player, None)
    translated_player.club = _get_player_club(player, None)
    #translated_player.league = _get_player_league(player, "Other")
    translated_player.league = "Unknown"
    translated_player.high_school = _get_meta_property(player, "high_school", None)
    translated_player.rating = _get_meta_property(player, "rating_player", None)
    translated_player.year = int(_get_meta_property(player, "graduation_year", None))
    translated_player.city = _get_player_city(player, None)
    translated_player.state = _get_meta_property(player, "state_province", None)
    translated_player.commitment = _get_player_commitment(player, None)
    translated_player.commitment_url = _get_player_commitment_url(player, None)

    if translated_player.high_school is None:
        translated_player.high_school = "Unknown"

    if len(translated_player.high_school) == 0:
        translated_player.high_school = "Unknown"

    if translated_player.position is None:
        translated_player.position = "Unknown"

    if len(translated_player.position) == 0:
        translated_player.position = "Unknown"

    if translated_player.city is None:
        translated_player.city = "Unknown"

    if len(translated_player.city) == 0:
        translated_player.city = "Unknown"

    if translated_player.club is None:
        translated_player.club = "Unknown"

    if len(translated_player.club) == 0:
        translated_player.club = "Unknown"

    if translated_player.state is None:
        translated_player.state = "Unknown"

    if len(translated_player.state) == 0:
        translated_player.state = "Unknown"

    if translated_player.commitment is None:
        translated_player.commitment = "Unknown"

    if len(translated_player.commitment) == 0:
        translated_player.commitment = "Unknown"

    if translated_player.commitment_url is None:
        translated_player.commitment_url = "Unknown"

    return translated_player


if __name__ == "__main__":
    genders = ["male", "female"]
    years = ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]

    players = []
    for gender in genders:
        for year in years:
            count = get_number_of_commitments(gender, year)
            payload = build_payload(gender, year, count)
            response = requests.post(URL, json=payload)
            data = response.json()

            file_name = f"{gender}.{year}.csv"

            # if the file exists already delete it
            try:
                os.remove(file_name)
            except FileNotFoundError:
                pass

            with open(file_name, 'w', newline='') as csvfile:
                player_writer = csv.writer(csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                player_writer.writerow(["Name", "Position", "Club", "High School", "City", "State", "Commitment", "Commitment URL"])
                for item in data["hits"]["hits"]:
                    player = _translate_player(item["_source"])
                    player_writer.writerow([player.name, player.position, player.club, player.high_school, player.city, player.state, player.commitment, player.commitment_url])
