import json
import sys

import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import *


def generate_url(rxcui):
    return f"https://rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcui={rxcui}"


def get_details_from_pair(interaction_pair):
    description = interaction_pair["description"]
    severity = interaction_pair["severity"]
    left, right = interaction_pair["interactionConcept"]
    left_name = left["sourceConceptItem"]["name"]
    left_sourceid = int(left["sourceConceptItem"]["id"][2:])
    left_rxcui = int(left["minConceptItem"]["rxcui"])
    right_name = right["sourceConceptItem"]["name"]
    right_sourceid = right["sourceConceptItem"]["id"][2:]
    right_rxcui = int(right["minConceptItem"]["rxcui"])
    left = {"name": left_name, "source_id": left_sourceid, "rxcui": left_rxcui}
    right = {"name": right_name, "source_id": right_sourceid, "rxcui": right_rxcui}
    return description, severity, left, right


def interaction_exists(left_drug, right_drug):
    exists = False
    if left_drug is not None and right_drug is not None:
        # both drug esists, now check for the interaction
        for interaction in left_drug.interactions:
            if right_drug in interaction.generics:
                # interaction already exists
                exists = True
                break
        for interaction in right_drug.interactions:
            if left_drug in interaction.generics:
                # interaction already exists
                exists = True
                break
    return exists


def process_one_pair(interaction_pair, session):
    description, severity, left, right = get_details_from_pair(interaction_pair)

    left_drug = session.scalar(select(Generic).filter_by(source_id=left["source_id"]))
    right_drug = session.scalar(select(Generic).filter_by(source_id=right["source_id"]))

    if left_drug is None:
        left_drug = Generic(
            rxcui=left["rxcui"], name=left["name"], source_id=left["source_id"]
        )
        print(f"Adding {left_drug} to database")
        session.add(left_drug)
    if right_drug is None:
        right_drug = Generic(
            rxcui=right["rxcui"], name=right["name"], source_id=right["source_id"]
        )
        print(f"Adding {right_drug} to database")
        session.add(right_drug)

    if not interaction_exists(left_drug, right_drug):
        interaction = Interaction(description=description)
        # interaction.generics.append(left_drug)
        # interaction.generics.append(right_drug)
        left_drug.interactions.append(interaction)
        right_drug.interactions.append(interaction)

        print(f"Adding interaction between {left['name']} and {right['name']}")
    else:
        print(f"Interaction between {left['name']} and {right['name']} already exists")


def populate_db(
    db_path="interaction.db",
    source_file_path="uniq_generic_ids.txt",
    start=None,
    end=None,
    log=False,
):
    succeeded, failed = [], []

    if log:
        import logging

        logging.basicConfig()
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    session = Session(engine)

    with open(source_file_path, "r") as file:
        generic_ids = list(filter(None, file.read().split("\n")))

    if start is None:
        start = 0
    if end is None:
        end = len(generic_ids)

    for i, id in enumerate(generic_ids[start:end]):
        url = generate_url(id)
        print(f"{i+start}: fetching {url}")
        try:
            data = requests.get(url).json()
        except Exception as e:
            print(f"[ERROR] failed to fetch {url} due to {e}")
            failed.append(id)
            continue
        if "interactionTypeGroup" in data:
            for interaction_group in data["interactionTypeGroup"]:
                if interaction_group["sourceName"] != "DrugBank":
                    continue
                for interaction_type in interaction_group["interactionType"]:
                    for interaction_pair in interaction_type["interactionPair"]:
                        process_one_pair(interaction_pair, session)
            print("committing changes to database")
            session.commit()
            succeeded.append(id)

    session.close()
    engine.dispose()
    return succeeded, failed


if __name__ == "__main__":
    populate_db()
