import os
import csv
import requests

from bs4 import BeautifulSoup, element

RPI_URL = "https://www.ncaa.com/rankings/soccer-women/d1/ncaa-womens-soccer-rpi"


class School:
    rank: int
    name: str
    conference: str
    record: str
    road: str
    neutral: str
    home: str
    non_div_1: str

    def __init__(self):
        self.rank = 0
        self.name = ""
        self.conference = ""
        self.record = ""
        self.road = ""
        self.neutral = ""
        self.home = ""
        self.non_div_1 = ""

    def __str__(self):
        return f"{self.rank}: {self.name} - {self.conference}"


class SchoolBuilder:
    instance: School

    def __init__(self):
        self.instance = None

    def build(self):
        self.instance = School()

    def build_rank(self, rank: int):
        self.instance.rank = rank

    def build_name(self, name: str):
        self.instance.name = name

    def build_conference(self, conference: str):
        self.instance.conference = conference

    def build_record(self, record: str):
        self.instance.record = record

    def build_road(self, road: str):
        self.instance.road = road

    def build_neutral(self, neutral: str):
        self.instance.neutral = neutral

    def build_home(self, home: str):
        self.instance.home = home

    def build_non_div_1(self, non_div_1: str):
        self.instance.non_div_1 = non_div_1

    def get_instance(self) -> School:
        return self.instance


class SchoolFactory:
    builder: SchoolBuilder

    def __init__(self, builder: SchoolBuilder):
        if builder is None:
            builder = SchoolBuilder()

        self.builder = builder

    def create_school(self, row: element) -> School:
        cells = row.find_all('td')

        self.builder.build()

        self.builder.build_rank(cells[0].text)
        self.builder.build_name(cells[1].text)
        self.builder.build_conference(cells[2].text)
        self.builder.build_record(cells[3].text)
        self.builder.build_road(cells[4].text)
        self.builder.build_neutral(cells[5].text)
        self.builder.build_home(cells[6].text)
        self.builder.build_non_div_1(cells[7].text)

        return self.builder.get_instance()


if __name__ == "__main__":
    builder = SchoolBuilder()
    factory = SchoolFactory(builder)

    response = requests.get(RPI_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_=['sticky', 'tablesorter', 'tablesorter-default'])
    body = table.find('tbody')
    rows = body.find_all('tr')

    schools = []
    for row in rows:
        schools.append(factory.create_school(row))

    if os.path.isfile("rpi.csv"):
        os.remove("rpi.csv")

    with open("rpi.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Name", "Conference", "Record", "Road", "Neutral", "Home", "Non-Div 1"])

        for school in schools:
            writer.writerow([school.rank, school.name, school.conference, school.record, school.road, school.neutral, school.home, school.non_div_1])
