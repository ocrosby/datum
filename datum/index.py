import os
import sys
import csv
import logging

logger = logging.getLogger(__name__)


def get_sidearm_roster(name: str, url: str) -> list:
    roster = []
    logger.info("Getting Sidearm roster for '%s'...", name)
    return roster


def get_roster(target_vendor: str, gender: str, url: str) -> list:
    roster = []

    if target_vendor == "Sidearm":
        logger.info("Getting roster for Sidearm '%s'...", url)
    elif target_vendor == "WMT":
        logger.info("Getting roster for WMT '%s'...", url)
    elif target_vendor == "PrestoSports":
        logger.info("Getting roster for PrestoSports '%s'...", url)
    else:
        logger.info("Skipping '%s' because vendor '%s' is not recognized.", url, vendor)
        return None

    return None


if __name__ == "__main__":
    log_file = "index.log"
    index_file = "../data/index.csv"

    if os.path.isfile(log_file):
        os.remove(log_file)

    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Starting ...")

    if not os.path.isfile(index_file):
        sys.exit(f"{index_file} not found.")

    with open(index_file, "r", encoding="UTF8") as file:
        reader = csv.DictReader(file)
        headings = reader.fieldnames

        for row in reader:
            short_name = row["Short Name"].strip()
            long_name = row["Long Name"].strip()
            vendor = row["Vendor"].strip()
            womens_soccer_url = row["WOSO URL"].strip()

            if vendor == "None":
                logger.info("Skipping '%s' because vendor is None.", long_name)
                continue

            if len(vendor) == 0:
                logger.info("Skipping '%s' because vendor is empty.", long_name)
                continue

            if womens_soccer_url == "None":
                logger.info("Skipping '%s' because there is no women's soccer program.", long_name)
                continue

            if vendor == "Sidearm":
                logger.info("Todo: process Sidearm '%s'...", long_name)
            elif vendor == "WMT":
                logger.info("Todo: process WMT '%s'...", long_name)
            elif vendor == "PrestoSports":
                logger.info("Todo: process PrestoSports '%s'...", long_name)
            else:
                logger.info("Skipping '%s' because vendor '%s' is not recognized.", long_name, vendor)
                continue

    logger.info("Finished")

