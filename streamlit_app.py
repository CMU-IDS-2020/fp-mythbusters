import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import nltk
import streamlit as st
from vega_datasets import data

import twitter.tweet_fetcher
import twitter.word_cloud
from twitter.state_data_aggregator import STATE_TO_CODE_MAP

DATA_DIR = "data"


@st.cache(allow_output_mutation=True)
def get_wordcloud(state=None, stopwords=None):
    wc = twitter.word_cloud.get_wordcloud(DATA_DIR, state, stopwords)
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
    nltk.download("stopwords")
    nltk.download("punkt")
    stopwords = nltk.corpus.stopwords.words("english")
    wordcloud = get_wordcloud(stopwords)
    st.pyplot(wordcloud)
    selected_state = draw_state_counties()
    state_wordcloud = get_wordcloud(STATE_TO_CODE_MAP[selected_state.strip()], stopwords)
    st.pyplot(state_wordcloud)
    st.write(
        "This is just a random tweet sampled from NY for prototype purpose. In the final project we may want to embed a couple of tweets from each state")
    html = '''
        <blockquote class="twitter-tweet"><p lang="en" dir="ltr"><a href="https://twitter.com/hashtag/CoronaVirusNYC?src=hash&amp;ref_src=twsrc%5Etfw">#CoronaVirusNYC</a> <a href="https://twitter.com/hashtag/ChinaLiedAndPeopleDied?src=hash&amp;ref_src=twsrc%5Etfw">#ChinaLiedAndPeopleDied</a> <br><br>You honestly still believe Chinese Communist Party regarding <a href="https://twitter.com/hashtag/CoronaVirus?src=hash&amp;ref_src=twsrc%5Etfw">#CoronaVirus</a> / <a href="https://twitter.com/hashtag/COVID%E3%83%BC19?src=hash&amp;ref_src=twsrc%5Etfw">#COVIDー19</a> originating from someone eating a Bat Burger from Food Market in <a href="https://twitter.com/hashtag/Wuhan?src=hash&amp;ref_src=twsrc%5Etfw">#Wuhan</a> after seeing this...!!!<br><br>To, mae <a href="https://twitter.com/hashtag/COVID19?src=hash&amp;ref_src=twsrc%5Etfw">#COVID19</a> is likely more tragic &amp; sinister... <a href="https://t.co/EvVI5SXD1U">https://t.co/EvVI5SXD1U</a></p>&mdash; Darren Williams (@DazAltTheory) <a href="https://twitter.com/DazAltTheory/status/1248540485733552128?ref_src=twsrc%5Etfw">April 10, 2020</a></blockquote>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    '''
    st.write('https://twitter.com/DazAltTheory/status/1248540485733552128')
    st.markdown(html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
