import os

state_map = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Puerto Rico": "PR",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virgin Islands": "VI",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY"
}

GEO_TWEET_ID_DIR = "../data/tweets/geo_covid_tweet_ids/geo"
GEO_TWEET_TEXT_DIR = "../data/tweets/geo_covid_tweets"


def aggregate():
    for state, code in state_map.items():
        aggregate_state(GEO_TWEET_ID_DIR, state, code)
        aggregate_state(GEO_TWEET_TEXT_DIR, state, code)


def aggregate_state(directory, state, code):
    if os.path.exists(f"{directory}/{state}.txt"):
        with open(f"{directory}/{state}.txt") as state_file:
            with open(f"{directory}/{code}.txt", "a+") as code_file:
                state_lines = state_file.readlines()
                code_file.writelines(state_lines)


def delete_state_files():
    for state, _ in state_map.items():
        delete_state_file(GEO_TWEET_ID_DIR, state)
        delete_state_file(GEO_TWEET_TEXT_DIR, state)


def delete_state_file(directory, state):
    file_name = f"{directory}/{state}.txt"
    if os.path.exists(file_name):
        os.remove(file_name)


if __name__ == "__main__":
    # aggregate()
    delete_state_files()
