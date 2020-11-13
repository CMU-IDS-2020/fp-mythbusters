import matplotlib.pyplot as plt
import streamlit as st

import twitter.word_cloud

import pandas as pd
import altair as alt
from vega_datasets import data

DATA_DIR = "data"
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


@st.cache(allow_output_mutation=True)
def get_wordcloud(state=None):
    wc = twitter.word_cloud.get_wordcloud(DATA_DIR, state)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    return fig


@st.cache(allow_output_mutation=True)  # add caching so we load the data only once
def load_state_fips():
    state_fips_df = pd.read_excel("data/covid_usafacts/raw/state_fips_2019.xlsx", skiprows=range(5))
    state_fips_df = state_fips_df[state_fips_df["State (FIPS)"] > 0]  # exclude regions, divisions, and non-state rows
    return state_fips_df[["State (FIPS)", "Name"]].sort_values("Name").set_index("Name").to_dict()["State (FIPS)"]


@st.cache(allow_output_mutation=True)
def load_state_usda():
    state_usda_dict = {
        "New York": pd.read_csv("data/usda_county_datasets/clean/ny_counties.csv", index_col=0),
        "Pennsylvania": pd.read_csv("data/usda_county_datasets/clean/pa_counties.csv", index_col=0)
    }
    return state_usda_dict


def draw_state_counties():
    state_usda_dict = load_state_usda()
    state_fips_dict = load_state_fips()

    states = list(state_usda_dict.keys())
    selected_state = st.selectbox('State', options=states, index=states.index("New York"))

    usda_df = state_usda_dict.get(selected_state)
    usda_features = [col for col in usda_df.columns if col not in ['FIPS', 'Name']]
    selected_usda_feature = st.selectbox('Based on', options=usda_features, index=0)

    counties = alt.topo_feature(data.us_10m.url, 'counties')
    state_map = alt.Chart(data=counties).mark_geoshape(stroke='black', strokeWidth=1) \
        .encode(color="%s:Q" % selected_usda_feature,
                tooltip=[alt.Tooltip('id:N', title='FIPS'),
                         alt.Tooltip('Name:N', title='County')]) \
        .transform_calculate(state_id="(datum.id / 1000)|0") \
        .transform_filter(alt.datum.state_id == state_fips_dict[selected_state]) \
        .transform_lookup(lookup='id', from_=alt.LookupData(usda_df, 'FIPS', [selected_usda_feature, 'Name'])) \
        .properties(width=650, height=650)
    st.write(state_map)
    return selected_state


def main():
    wordcloud = get_wordcloud()
    st.pyplot(wordcloud)
    selected_state = draw_state_counties()
    # TODO we can shape these wordclouds to any shape we want, it would be sick to shape them like the state they're from
    state_wordcloud = get_wordcloud(state_map[selected_state.strip()])
    st.pyplot(state_wordcloud)


if __name__ == "__main__":
    main()
