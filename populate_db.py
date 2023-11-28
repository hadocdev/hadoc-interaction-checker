import json
import pickle
import sys

import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import *


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


generics = []
source_ids = []


def process_item(item, session):
    description, left, right = item
    for item in (left, right):
        if item["source_id"] not in source_ids:
            drug = Generic(
                rxcui=item["rxcui"], name=item["name"], source_id=item["source_id"]
            )
            source_ids.append(item["source_id"])
            generics.append(drug)

    left_drug = generics[source_ids.index(left["source_id"])]
    right_drug = generics[source_ids.index(right["source_id"])]
    if not interaction_exists(left_drug, right_drug):
        interaction = Interaction(description=description)
        left_drug.interactions.append(interaction)
        right_drug.interactions.append(interaction)


def populate_db(
    db_path="interaction.db",
    pickle_file_path="data.pickle",
    start=None,
    end=None,
    log=False,
):
    if log:
        import logging

        logging.basicConfig()
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    session = Session(engine)

    with open(pickle_file_path, "rb") as file:
        print(f"Reading {pickle_file_path}. This may take a while.")
        data = pickle.load(file)
    if start is None:
        start = 0
    if end is None:
        end = len(data)

    i = start
    for key, value in data.items():
        if i == end:
            break
        print(f"{i}: processing interactions for rxcui={key}")
        for item in value:
            process_item(item, session)
        i += 1
    session.add_all(generics)
    print("committing changes to database")
    session.commit()

    session.close()
    engine.dispose()


if __name__ == "__main__":
    populate_db()
