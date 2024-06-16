import re
import os
import csv
import requests

from bs4 import BeautifulSoup

URL = "https://www.topdrawersoccer.com/college-soccer-articles/2024-womens-division-i-transfer-tracker_aid52845"


def translate_position(position: str) -> str:
    if position == "GK":
        return "Goalkeeper"
    elif position == "D":
        return "Defender"
    elif position == "M":
        return "Midfielder"
    elif position == "F":
        return "Forward"
    elif position == "F/M":
        return "Forward/Midfielder"
    elif position == "F/D":
        return "Forward/Defender"
    elif position == "M/D":
        return "Midfielder/Defender"
    elif position == "D/M":
        return "Defender/Midfielder"
    else:
        return position


if __name__ == "__main__":
    if os.path.isfile("transfers.csv"):
        os.remove("transfers.csv")

    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.find_all("tr")

    data = []

    with open("transfers.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Position", "Outgoing College", "Incoming College"])

        for row in rows:
            cells = row.find_all("td")

            if len(cells) == 0:
                continue

            temp = cells[0].text.strip()

            if temp == "Name":
                continue

            # the temp value contains a position followed by a first name and last name separated by spaces
            # we need to get the position and the name separately
            try:
                position, name = re.split(r'\s', temp, 1)
            except ValueError:
                if len(temp) == 0:
                    continue

                print(f"Error splitting position and name: {temp}")
                continue

            position = translate_position(position)

            if name == "Blum":
                pass

            outgoing_college = cells[1].text.strip()
            incoming_college = cells[2].text.strip()

            data.append((name, position, outgoing_college, incoming_college))

            try:
                writer.writerow([name, position, outgoing_college, incoming_college])
            except AttributeError as err:
                print(f"Error writing row: {err}")
                print(f"Name: {name}")
            except UnicodeEncodeError as err:
                print(f"Error writing row: {err}")
                print(f"Name: {name}")

    # Determine a unqiue list of colleges
    colleges = set()
    for _, _, outgoing_college, incoming_college in data:
        colleges.add(outgoing_college)
        colleges.add(incoming_college)

    # Determine the outgoing frequency and incoming frequency of each college
    outgoing_frequency = {}
    incoming_frequency = {}
    for college in colleges:
        outgoing_frequency[college] = 0
        incoming_frequency[college] = 0

    for _, _, outgoing_college, incoming_college in data:
        outgoing_frequency[outgoing_college] += 1
        incoming_frequency[incoming_college] += 1


    # I need to go through all the frequencies highest to lowest collecting all colleges
    # with the same frequency

    # Sort the colleges by outgoing frequency
    outgoing_frequency = dict(sorted(outgoing_frequency.items(), key=lambda item: item[1], reverse=True))

    # Sort the colleges by incoming frequency
    incoming_frequency = dict(sorted(incoming_frequency.items(), key=lambda item: item[1], reverse=True))

    # print all the colleges by frequency

    print("Outgoing Frequency")
    for college, frequency in outgoing_frequency.items():
        if frequency == 0:
            continue

        print(f"{college}: {frequency}")

    print("\nIncoming Frequency")
    for college, frequency in incoming_frequency.items():
        if frequency == 0:
            continue

        print(f"{college}: {frequency}")


    print("Done!")

# Path: projects/topdrawer/players.py



