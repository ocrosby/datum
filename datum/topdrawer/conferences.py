import os
import csv
import requests

from dataclasses import dataclass
from typing import List, Tuple
from bs4 import BeautifulSoup

GENDERS = ["male", "female"]

DIVISIONS = ["di", "dii", "diii", "naia", "njcaa"]

DIVISION_TO_URL_MAP = {
    "di": "https://www.topdrawersoccer.com/college-soccer/college-conferences/di/divisionid-1",
    "dii": "https://www.topdrawersoccer.com/college-soccer/college-conferences/dii/divisionid-2",
    "diii": "https://www.topdrawersoccer.com/college-soccer/college-conferences/diii/divisionid-3",
    "naia": "https://www.topdrawersoccer.com/college-soccer/college-conferences/naia/divisionid-4",
    "njcaa": "https://www.topdrawersoccer.com/college-soccer/college-conferences/njcaa/divisionid-5"
}


@dataclass
class Program:
    id: str | None
    school_name: str | None
    gender: str | None
    url: str | None

    def __init__(self):
        self.id = None
        self.school_name = None
        self.gender = None
        self.url = None

    def __str__(self):
        if self.gender == "male":
            return f"{self.school_name} (Men's)"
        elif self.gender == "female":
            return f"{self.school_name} (Women's)"
        else:
            return self.school_name


@dataclass
class Conference:
    id: str | None
    name: str | None
    gender: str | None
    division: str | None
    url: str | None

    def __init__(self):
        self.name = None
        self.gender = None
        self.division = None
        self.url = None

    def __str__(self):
        return f"{self.division}:{self.name}:{self.gender}: {self.url}"

    def __repr__(self):
        return str(self)

    def dump(self):
        pass


class ConferenceReader:
    def __init__(self):
        pass

    def read(self, gender: str, division: str) -> List[Conference]:
        if gender not in ["all", "male", "female"]:
            raise ValueError(f"Invalid gender: {gender}")

        url = DIVISION_TO_URL_MAP.get(division, None)

        print(f"URL: {url}")

        if url is None:
            raise ValueError(f"Invalid division: {division}")

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        columns = soup.find_all("div", class_="col-lg-6")

        conferences = []
        for column in columns:
            title = column.find("h1", class_="title-context").text

            current_gender = None
            if "Men's" in title:
                current_gender = "male"
            elif "Women's" in title:
                current_gender = "female"

            should_include = (gender == "all") or (gender == current_gender)

            if not should_include:
                continue

            rows = column.find_all("tr")
            for row in rows:
                conference = Conference()

                anchor = row.find("a")
                conference.gender = current_gender
                conference.name = anchor.text.strip()
                conference.division = division
                conference.url = "https://www.topdrawersoccer.com" + anchor.get("href").strip()
                conference.id = conference.url.split('-')[-1]

                conferences.append(conference)

        return conferences


class ConferenceWriter:
    def __init__(self):
        pass

    def write(self, gender: str, division: str, conferences: List[Conference]) -> None:
        output_file = f"conferences_{division}_{gender}.csv"

        if os.path.exists(output_file):
            os.remove(output_file)

        with open(output_file, "w") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "Name", "Division", "Gender", "URL"])

            for conference in conferences:
                writer.writerow([conference.id,
                                 conference.name,
                                 conference.division,
                                 conference.gender,
                                 conference.url])


class ProgramReader:
    def __init__(self):
        pass

    def read(self, conference: Conference) -> List[Program]:
        response = requests.get(conference.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        programs = []

        columns = soup.find_all("div", class_="col-lg-6")
        for column in columns:
            title = column.find("h1", class_="title-context").text.strip()

            if not "Conference Standings" in title:
                continue

            table = column.find("table", class_="table-striped")
            rows = table.find_all("tr")
            for row in rows:
                program = Program()
                program.gender = conference.gender

                anchor = row.find("a")

                if anchor is None:
                    print(row)
                    continue

                program.school_name = anchor.text.strip()
                program.url = "https://www.topdrawersoccer.com" + anchor.get("href").strip()
                program.id = program.url.split('-')[-1]

                programs.append(program)

        return programs


if __name__ == "__main__":
    conference_reader = ConferenceReader()
    conference_writer = ConferenceWriter()
    program_reader = ProgramReader()

    for division in DIVISIONS:
        for gender in GENDERS:
            conferences = conference_reader.read(gender, division)
            conference_writer.write(gender, division, conferences)

            for conference in conferences:
                print(conference)
                programs = program_reader.read(conference)
                for program in programs:
                    print(f"\t{program}")
