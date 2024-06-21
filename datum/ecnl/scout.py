"""
This code is written based of evaluations from

https://public.totalglobalsports.com/public/event/3064/college-list
"""

from __future__ import annotations
from dataclasses import dataclass

import os
import csv
import requests

import datum.tgs.event

# from typing import List, Tuple, Optional


@dataclass
class Coach:
    id: str
    collegeId: int
    userRoleId: int
    firstName: str
    lastName: str
    email: str
    phone: str
    role: str
    roleId: int
    userId: int
    userImage: str
    collegeProgramId: int
    publish: int
    statusId: int
    publicEmail: str
    publicEmailDisplayEnabled: int


@dataclass
class Program:
    programId: int
    description: str
    collegeId: int
    sportId: int
    eventId: int
    collegeName: str
    city: str
    type: str
    logo: str
    statecode: str
    conferenceName: str
    collegeDivisionId: int
    collegeDivisionName: str
    gender: str
    webSite: str
    status: str
    publish: int
    stateId: int
    collegeConferenceId: int
    coaches: list[Coach]


@dataclass
class Division:
    id: int
    name: str


@dataclass
class Conference:
    id: int
    divisionId: int
    name: str


@dataclass
class State:
    id: int
    regionId: int | None
    countryId: int | None
    code: str
    name: str
    image: str
    timeZoneId: str


@dataclass
class Event:
    eventID: int
    eventLogo: str
    eventPublicBanner: str | None
    eventBGImage: str | None
    eventBGColor: str
    name: str
    description: str | None
    feeSummary: str
    orgTypeID: int
    regStartDate: str | None
    regEndDate: str | None
    regStatus: bool
    regStatusText: str
    location: str
    address: str
    city: str
    zip: str
    stateID: int
    eventSubTypeID: int
    eventStartDate: str
    eventEndDate: str
    eventFeatures: str | None
    tournamentPurchaseCost: int
    paymentDate: str
    transactionID: str | None
    cardType: str | None
    maskedCardNum: str | None
    originalAmount: str | None
    discountAmount: str | None
    orgID: int
    appID: str
    stateCode: str
    programs: list[Program]


def get_college_division_list() -> list[Division]:
    url = "https://public.totalglobalsports.com/api/player/get-college-division-list"
    response = requests.get(url, timeout=10)
    data = response.json()

    divisions = []
    for item in data["data"]:
        division = Division(id=item["collegeDivisionID"], name=item["collegeDivisionName"])
        divisions.append(division)

    return divisions


def get_college_conference_list() -> list[Conference]:
    url = "https://public.totalglobalsports.com/api/player/get-college-conference-list"
    response = requests.get(url, timeout=10)
    data = response.json()

    conferences = []
    for item in data["data"]:
        conference = Conference(id=item["collegeconferenceID"],
                                divisionId=item["collegedivisionID"],
                                name=item["conferencename"])
        conferences.append(conference)

    return conferences


def get_all_states() -> list[State]:
    url = "https://public.totalglobalsports.com/api/player/get-all-states"

    response = requests.get(url, timeout=10)
    data = response.json()

    states = []
    for item in data["data"]:
        state = State(id=item["stateID"],
                      regionId=item["regionID"],
                      countryId=item["countryID"],
                      code=item["stateCode"],
                      name=item["stateName"],
                      image=item["stateImage"],
                      timeZoneId=item["timeZoneID"])
        states.append(state)

    return states


def get_event_by_id(eventId: int) -> Event:
    # url = f"https://public.totalglobalsports.com/public/event/{eventId}/college-list"
    url = f"https://public.totalglobalsports.com/api/Event/get-event-details-by-eventID/{eventId}"

    response = requests.get(url, timeout=10)
    data = response.json().get("data")

    event = Event(eventID=data["eventID"],
                  eventLogo=data["eventLogo"],
                  eventPublicBanner=data["eventPublicBanner"],
                  eventBGImage=data["eventBGImage"],
                  eventBGColor=data["eventBGColor"],
                  name=data["name"],
                  description=data["description"],
                  feeSummary=data["feeSummary"],
                  orgTypeID=data["orgTypeID"],
                  regStartDate=data["regStartDate"],
                  regEndDate=data["regEndDate"],
                  regStatus=data["regStatus"],
                  regStatusText=data["regStatusText"],
                  location=data["location"],
                  address=data["address"],
                  city=data["city"],
                  zip=data["zip"],
                  stateID=data["stateID"],
                  eventSubTypeID=data["eventSubTypeID"],
                  eventStartDate=data["eventStartDate"],
                  eventEndDate=data["eventEndDate"],
                  eventFeatures=data["eventFeatures"],
                  tournamentPurchaseCost=data["tournamentPurchaseCost"],
                  paymentDate=data["paymentDate"],
                  transactionID=data["transactionID"],
                  cardType=data["cardType"],
                  maskedCardNum=data["maskedCardNum"],
                  originalAmount=data["originalAmount"],
                  discountAmount=data["discountAmount"],
                  orgID=data["orgID"],
                  appID=data["appID"],
                  stateCode=data["stateCode"],
                  programs=[])

    return event


def get_attending_programs(event_id: int) -> list[Program]:
    url = f"https://public.totalglobalsports.com/api/Event/get-colleges-attending-list-with-coaches-by-event/{event_id}"
    response = requests.get(url, timeout=10)
    data = response.json()

    infos = []
    for item in data["data"]:
        info = Program(programId=item["collegeInfo"]["collegeprogramID"],
                       description=item["collegeInfo"]["description"],
                       collegeId=item["collegeInfo"]["collegeID"],
                       sportId=item["collegeInfo"]["sportID"],
                       eventId=item["collegeInfo"]["eventID"],
                       collegeName=item["collegeInfo"]["collegename"],
                       city=item["collegeInfo"]["city"],
                       type=item["collegeInfo"]["type"],
                       logo=item["collegeInfo"]["logo"],
                       statecode=item["collegeInfo"]["statecode"],
                       conferenceName=item["collegeInfo"]["conferencename"],
                       collegeDivisionId=item["collegeInfo"]["collegeDivisionID"],
                       collegeDivisionName=item["collegeInfo"]["collegedivisionname"],
                       gender=item["collegeInfo"]["gender"],
                       webSite=item["collegeInfo"]["webSite"],
                       status=item["collegeInfo"]["status"],
                       publish=item["collegeInfo"]["publish"],
                       stateId=item["collegeInfo"]["stateID"],
                       collegeConferenceId=item["collegeInfo"]["collegeConferenceID"],
                       coaches=[])

        for coach in item["coachList"]:
            c = Coach(id=coach["id"],
                      collegeId=coach["collegeid"],
                      userRoleId=coach["userRoleID"],
                      firstName=coach["firstname"],
                      lastName=coach["lastname"],
                      email=coach["email"],
                      phone=coach["phone"],
                      role=coach["role"],
                      roleId=coach["roleID"],
                      userId=coach["userid"],
                      userImage=coach["userImage"],
                      collegeProgramId=coach["collegeprogramID"],
                      publish=coach["publish"],
                      statusId=coach["statusID"],
                      publicEmail=coach["publicEmail"],
                      publicEmailDisplayEnabled=coach["publicEmailDisplayEnabled"])

            info.coaches.append(c)

        infos.append(info)

    return infos


def process_event(eventId: int,
                  states: list[State],
                  divisions: list[Division],
                  conferences: list[Conference],
                  events: list[Event],
                  programs: list[Program],
                  coaches: list[Coach]):

    event_info = datum.tgs.event.get_by_id(eventId)

    event = get_event_by_id(eventId)

    # Don't add duplicate event names
    if not any(e.name == event.name for e in events):
        events.append(event)

    programs = get_attending_programs(eventId)


    output_file = f"{eventId}_scout.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, "w", newline="", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(["College Name", "City", "State", "URL", "Name", "Role", "Email", "Phone"])

        for program in programs:
            event.programs.append(program)

            for coach in program.coaches:
                writer.writerow([program.collegeName,
                                 program.city,
                                 program.statecode,
                                 program.webSite,
                                 f"{coach.firstName} {coach.lastName}",
                                 coach.role,
                                 coach.email,
                                 coach.phone])

                # Check if event is already in events
                if not any(e.name == event.name for e in events):
                    events.append(event)

                # Check if program is already in programs
                if not any(p.collegeName == program.collegeName for p in programs):
                    programs.append(program)

                # Check if coach is already in coaches
                if not any(c.firstName == coach.firstName and c.lastName == coach.lastName for c in coaches):
                    coaches.append(coach)


def save_divisions(divisions: list[Division]):
    output_file = "divisions.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, "w", newline="", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name"])

        for division in divisions:
            writer.writerow([division.id, division.name])


def save_conferences(conferences: list[Conference]):
    output_file = "conferences.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, "w", newline="", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Division ID", "Name"])

        for conference in conferences:
            writer.writerow([conference.id, conference.divisionId, conference.name])

def save_states(states: list[State]):
    output_file = "states.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, "w", newline="", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Code", "Image", "Time Zone ID"])

        for state in states:
            writer.writerow([state.id, state.name, state.code, state.image, state.timeZoneId])


def save_scouts(states: list[State], divisions: list[Division], conferences: list[Conference], events: list[Event], programs: list[Program], coaches: list[Coach], accumulator: list[tuple[Program, Coach]]):
    output_file = "scout.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    # Sort the accumulator by college name then by coach name
    accumulator.sort(key=lambda x: (x[0].collegeName, x[1].lastName, x[1].firstName))

    with open(output_file, "w", newline="", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(["College Name", "Division", "Conference", "City", "State", "URL", "Name", "Role", "Email", "Phone"])

        for program, coach in accumulator:
            writer.writerow([program.collegeName,
                             program.collegeDivisionName,
                             program.conferenceName,
                             program.city,
                             program.statecode,
                             program.webSite,
                             f"{coach.firstName} {coach.lastName}",
                             coach.role,
                             coach.email,
                             coach.phone])


if __name__ == "__main__":
    events = []
    programs = []
    coaches = []

    divisions = get_college_division_list()
    conferences = get_college_conference_list()
    states = get_all_states()

    accumulator = []

    save_divisions(divisions)
    save_conferences(conferences)
    save_states(states)

    process_event(3009, states, divisions, conferences, events, programs, coaches)
    process_event(3010, states, divisions, conferences, events, programs, coaches)
    process_event(2992, states, divisions, conferences, events, programs, coaches)
    process_event(3016, states, divisions, conferences, events, programs, coaches)
    process_event(3028, states, divisions, conferences, events, programs, coaches)
    process_event(3030, states, divisions, conferences, events, programs, coaches)
    process_event(3031, states, divisions, conferences, events, programs, coaches)
    process_event(3033, states, divisions, conferences, events, programs, coaches)
    process_event(3035, states, divisions, conferences, events, programs, coaches)
    process_event(3036, states, divisions, conferences, events, programs, coaches)
    process_event(3064, states, divisions, conferences, events, programs, coaches)

    # Sort the accumulator by college name then by coach name
    accumulator.sort(key=lambda x: (x[0].collegeDivisionName,
                                    x[0].conferenceName,
                                    x[0].collegeName,
                                    x[1].lastName,
                                    x[1].firstName))

    save_scouts(states, divisions, conferences, events, programs, coaches, accumulator)

