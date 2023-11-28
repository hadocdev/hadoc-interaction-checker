import pickle

import requests

source_file_path = "./uniq_generic_ids.txt"
with open(source_file_path, "r") as file:
    generic_ids = list(filter(None, file.read().split("\n")))

alldata = {}

for i, rxcui in enumerate(generic_ids):
    url = f"https://rxnav.nlm.nih.gov/REST/interaction/interaction.json?rxcui={rxcui}"
    print(f"{i+1}: fetching {url}")
    data = requests.get(url).json()
    if "interactionTypeGroup" in data:
        for interaction_group in data["interactionTypeGroup"]:
            if interaction_group["sourceName"] != "DrugBank":
                continue
            alldata[rxcui] = []
            for interaction_type in interaction_group["interactionType"]:
                for interaction_pair in interaction_type["interactionPair"]:
                    description = interaction_pair["description"]
                    left, right = interaction_pair["interactionConcept"]
                    left_name = left["sourceConceptItem"]["name"]
                    left_sourceid = int(left["sourceConceptItem"]["id"][2:])
                    left_rxcui = int(left["minConceptItem"]["rxcui"])
                    right_name = right["sourceConceptItem"]["name"]
                    right_sourceid = int(right["sourceConceptItem"]["id"][2:])
                    right_rxcui = int(right["minConceptItem"]["rxcui"])
                    left = {
                        "name": left_name,
                        "source_id": left_sourceid,
                        "rxcui": left_rxcui,
                    }
                    right = {
                        "name": right_name,
                        "source_id": right_sourceid,
                        "rxcui": right_rxcui,
                    }

                    alldata[rxcui].append([description, left, right])

        print(f"saving data containing {len(alldata.keys())} items")
        with open("data.pickle", "wb") as file:
            pickle.dump(alldata, file)
