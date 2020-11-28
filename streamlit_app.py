from datetime import timedelta

import altair as alt
import matplotlib.pyplot as plt
import nltk
import pandas as pd
import streamlit as st
from vega_datasets import data
import numpy as np

import twitter.tweet_fetcher
import twitter.word_cloud
from twitter.state_data_aggregator import STATE_TO_CODE_MAP
from twitter.tweet_fetcher import get_saved_tweet_oembeds

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
    state_fips = pd.read_csv("data/fips/clean/state_fips_2019.csv", index_col=0)
    state_fips = state_fips[state_fips["State FIPS"] > 0]  # exclude regions, divisions, and non-state rows
    return state_fips[["State FIPS", "Name"]].sort_values("Name").set_index("Name").to_dict()["State FIPS"]


@st.cache(allow_output_mutation=True)
def load_usda_data():
    poverty = pd.read_csv("data/usda_county_datasets/clean/poverty_2018.csv", index_col=0)
    unemployment_median_hhi = pd.read_csv("data/usda_county_datasets/clean/unemployment_median_hhi_2018.csv",
                                          index_col=0)
    population = pd.read_csv("data/usda_county_datasets/clean/population_2018.csv", index_col=0)
    education = pd.read_csv("data/usda_county_datasets/clean/education_2018.csv", index_col=0)
    usda_data = {
        'Poverty': poverty,
        'Unemployment and Median HHI': unemployment_median_hhi,
        'Population': population,
        'Education': education
    }
    return usda_data


@st.cache(allow_output_mutation=True)
def load_covid_data():
    # Read in data from local csv files
    confirmed_cumulative_cases_prop_fips = pd.read_csv(
        "data/covid_usafacts/clean/confirmed_cumulative_cases_props_fips.csv", index_col=0)
    confirmed_daily_incidence_cases_prop_fips = pd.read_csv(
        "data/covid_usafacts/clean/confirmed_daily_incidence_cases_prop_fips.csv", index_col=0)
    cumulative_deaths_prop_fips = pd.read_csv("data/covid_usafacts/clean/cumulative_deaths_prop_fips.csv", index_col=0)
    daily_incidence_deaths_prop_fips = pd.read_csv("data/covid_usafacts/clean/daily_incidence_deaths_prop_fips.csv",
                                                   index_col=0)

    # Remove rows with values < 0.0 (not possible)
    confirmed_cumulative_cases_prop_fips = confirmed_cumulative_cases_prop_fips[
        confirmed_cumulative_cases_prop_fips["value"] >= 0.0]
    confirmed_daily_incidence_cases_prop_fips = confirmed_daily_incidence_cases_prop_fips[
        confirmed_daily_incidence_cases_prop_fips["value"] >= 0.0]
    cumulative_deaths_prop_fips = cumulative_deaths_prop_fips[cumulative_deaths_prop_fips["value"] >= 0.0]
    daily_incidence_deaths_prop_fips = daily_incidence_deaths_prop_fips[
        daily_incidence_deaths_prop_fips["value"] >= 0.0]

    # Convert all time_value columns into datetime
    confirmed_cumulative_cases_prop_fips["time_value"] = pd.to_datetime(
        confirmed_cumulative_cases_prop_fips["time_value"])
    confirmed_daily_incidence_cases_prop_fips["time_value"] = pd.to_datetime(
        confirmed_daily_incidence_cases_prop_fips["time_value"])
    cumulative_deaths_prop_fips["time_value"] = pd.to_datetime(cumulative_deaths_prop_fips["time_value"])
    daily_incidence_deaths_prop_fips["time_value"] = pd.to_datetime(daily_incidence_deaths_prop_fips["time_value"])

    # Only fetch most recent cumulative data
    confirmed_cumulative_cases_prop_fips = confirmed_cumulative_cases_prop_fips.sort_values("time_value")
    confirmed_cumulative_cases_prop_fips = confirmed_cumulative_cases_prop_fips[
        ~confirmed_cumulative_cases_prop_fips.duplicated("FIPS", keep='last')]
    cumulative_deaths_prop_fips = cumulative_deaths_prop_fips.sort_values("time_value")
    cumulative_deaths_prop_fips = cumulative_deaths_prop_fips[
        ~cumulative_deaths_prop_fips.duplicated("FIPS", keep='last')]

    covid_data = {
        'Cumulative Cases': confirmed_cumulative_cases_prop_fips,
        'Daily New Cases': confirmed_daily_incidence_cases_prop_fips,
        'Cumulative Deaths': cumulative_deaths_prop_fips,
        'Daily Deaths': daily_incidence_deaths_prop_fips
    }

    return covid_data


@st.cache(allow_output_mutation=True)
def get_covid_date_ranges(covid_data):
    covid_date_ranges = {}
    for covid_feature, df in covid_data.items():
        covid_date_ranges[covid_feature] = df["time_value"].min(), df["time_value"].max()
    return covid_date_ranges


def get_state_map_base(counties, selected_state_fips, selector):
    return alt.Chart(data=counties)\
        .mark_geoshape(stroke='black', strokeWidth=1)\
        .transform_calculate(state_id="(datum.id/1000)|0")\
        .transform_filter(alt.datum.state_id == selected_state_fips)\
        .properties(width=400, height=400)\
        .add_selection(selector)\
        .encode(stroke=alt.condition(selector, alt.value('purple'), alt.value('black')),
                strokeWidth=alt.condition(selector, alt.StrokeWidthValue(2.5), alt.StrokeWidthValue(1.0)))


def get_specific_state_map(state_map_base, selected_feature, selected_feature_label, lookup_df, lookup_fields):
    return state_map_base.encode(color="%s:Q" % selected_feature,
                                 tooltip=[alt.Tooltip('id:N', title='FIPS'),
                                          alt.Tooltip('Area Name:N', title='Location'),
                                          alt.Tooltip('%s:Q' % selected_feature, title=selected_feature_label)])\
        .transform_lookup(lookup='id', from_=alt.LookupData(lookup_df, 'FIPS', [selected_feature] + lookup_fields))


def draw_state_counties():
    counties = alt.topo_feature(data.us_10m.url, 'counties')

    # Select US state to view
    state_fips_dict = load_state_fips()
    states = list(state_fips_dict.keys())
    selected_state = st.sidebar.selectbox('US State', options=states, index=states.index("New York"))
    selected_state_fips = state_fips_dict.get(selected_state)

    col1, col2 = st.beta_columns(2)

    # ----- Create USDA feature state map -----

    # Load USDA data
    usda_data = load_usda_data()

    # Select USDA category
    selected_usda_category = col1.selectbox('Based on', options=list(usda_data.keys()), index=0)

    # Select USDA category feature to color choropleth map
    usda_df = usda_data.get(selected_usda_category)
    usda_df = usda_df[usda_df["FIPS"] % 1000 != 0]  # remove non-county rows
    usda_df = usda_df[usda_df["FIPS"] // 1000 == selected_state_fips]  # filter for only counties in the selected state
    usda_features = [col for col in usda_df.columns if col not in ['FIPS', 'State Abrv', 'Area Name']]
    selected_usda_feature = col1.selectbox('USDA Feature', options=usda_features, index=0)

    # Create state map based on USDA feature
    county_selector = alt.selection_single(on='mouseover', empty="none", fields=["id"])
    state_map_base = get_state_map_base(counties, selected_state_fips, county_selector)
    usda_state_map = get_specific_state_map(state_map_base,
                                            selected_feature=selected_usda_feature,
                                            selected_feature_label='Value',
                                            lookup_df=usda_df, lookup_fields=['Area Name'])
    usda_state_map = usda_state_map.properties(
        title="%s: %s" % (selected_usda_category, selected_usda_feature)
    )

    # ----- Create COVID feature state map -----
    # Load COVID data
    covid_data = load_covid_data()
    covid_date_ranges = get_covid_date_ranges(covid_data)

    # Select covid feature
    selected_covid_feature = col2.selectbox('COVID Feature per 100,000 population', options=list(covid_data.keys()), index=0)
    covid_df = covid_data.get(selected_covid_feature)
    covid_df = covid_df[covid_df["FIPS"] // 1000 == selected_state_fips]  # filter for only counties in the selected state

    time_series = False  # only do time series if we have a daily statistic

    if 'Daily' in selected_covid_feature:
        time_series = True

        # Select date range
        min_date, max_date = covid_date_ranges.get(selected_covid_feature)

        selected_min_date = col2.date_input("From Date", value=max_date-timedelta(days=7), min_value=min_date, max_value=max_date, key="min_date")
        selected_max_date = col2.date_input("To Date", value=max_date, min_value=min_date, max_value=max_date, key="max_date")
        if selected_min_date > selected_max_date:
            st.error("ERROR: 'From Date' must be earlier or equal to 'To Date'")

        # Select function for values in date range
        covid_date_range_functions = ["Max", "Min", "Average", "Median"]
        selected_agg_function = col2.selectbox("Statistic for date range", options=covid_date_range_functions, index=covid_date_range_functions.index("Max"))

        # Select rows within date range
        covid_df_pre_group = covid_df[(covid_df["time_value"] >= pd.Timestamp(selected_min_date)) & (covid_df["time_value"] <= pd.Timestamp(selected_max_date))]

        # Calculate aggregates for values in date range
        covid_df = covid_df_pre_group.groupby(['FIPS', 'Area Name'])['value']\
            .agg(Min='min', Max='max', Average='mean', Median='median')\
            .reset_index()

        # Create covid map based on COVID feature
        covid_state_map = get_specific_state_map(state_map_base,
                                                 selected_feature=selected_agg_function,
                                                 selected_feature_label=selected_agg_function,
                                                 lookup_df=covid_df, lookup_fields=['time_value', 'issue', 'Area Name'])
        covid_state_map = covid_state_map.properties(
            title="%s per 100,000 population" % selected_covid_feature
        )

    else:
        col2.selectbox('Cumulative as of', options=[covid_date_ranges.get(selected_covid_feature)[1].strftime("%B %d, %Y")])
        covid_state_map = get_specific_state_map(state_map_base,
                                                 selected_feature='value',
                                                 selected_feature_label='Value',
                                                 lookup_df=covid_df, lookup_fields=['time_value', 'issue', 'Area Name'])
        covid_state_map = covid_state_map.properties(
            title="%s per 100,000 population" % selected_covid_feature
        )

        # find correlation between the feature and the COVID stats
        full_df = covid_df.merge(usda_df, on="FIPS")
        correlation = np.corrcoef(full_df["value"], full_df[selected_usda_feature])

    # draw maps side-by-side
    st.write(alt.hconcat(usda_state_map, covid_state_map).resolve_scale(color='independent').configure_legend(orient='bottom'))

    if time_series:
        # time series stuff
        st.write("Time series analysis for covid cases")
        county_names = ["all counties"] + list(np.unique(covid_df_pre_group["Area Name"]))
        selected_county = st.multiselect("Counties", options=county_names, default="all counties")
        if "all counties" in selected_county:
            covid_df_time_series = covid_df_pre_group.copy()
        else:
            covid_df_time_series = covid_df_pre_group[covid_df_pre_group["Area Name"].isin(selected_county)]

        time_series_chart = alt.Chart(covid_df_time_series).mark_line().encode(
            x=alt.X('time_value:T', axis=alt.Axis(title="Day", format=("%b %d, %Y"), labelAngle=-90)),
            y=alt.Y('value:Q', axis=alt.Axis(title="%s" % selected_covid_feature)),
            color=alt.Color("Area Name", legend=None),
            tooltip=[alt.Tooltip('Area Name:N', title="County")]
        ).properties(width=900, height=500)

        st.write(time_series_chart)
    else:
        # TODO: to make more of a "narrative", could have a table for each state and the correlation
        st.write("Correlation between %s per 100,000 and %s: %.4f" % (selected_covid_feature, selected_usda_feature, correlation[0,1]))
        corr_plot = alt.Chart(full_df).mark_point().encode(
            x=alt.X("value:Q", axis=alt.Axis(title=selected_covid_feature+" per 100,000")),
            y=selected_usda_feature+":Q",
            tooltip=[alt.Tooltip("Area Name_x:N", title="County")]
        ).properties(width=800, height=500)
        corr_plot = corr_plot+corr_plot.transform_regression("value", selected_usda_feature, method="linear").mark_line(color="#000000")
        st.write(corr_plot)

    return selected_state


def draw_embedded_tweets(state):
    tweet_oembeds = get_saved_tweet_oembeds(DATA_DIR, state)
    with st.beta_expander("Example Tweets"):
        num_tweets = len(tweet_oembeds)
        half_num = int(num_tweets / 2)
        # Two rows are good for now with 6 tweets
        row1 = st.beta_columns(half_num) if half_num > 0 else []
        row2 = st.beta_columns(num_tweets - half_num) if num_tweets - half_num > 0 else []
        for i in range(num_tweets):
            if i < half_num:
                with row1[i]:
                    st.markdown(tweet_oembeds[i], unsafe_allow_html=True)
            else:
                with row2[i - half_num]:
                    st.markdown(tweet_oembeds[i], unsafe_allow_html=True)


def main():

    # Source for adjusting container width in streamlit app
    # https://discuss.streamlit.io/t/where-to-set-page-width-when-set-into-non-widescreeen-mode/959/2

    st.markdown(
        f"""
        <style>
            .reportview-container .main .block-container{{
               max-width: 1200px;
              padding-top: 5rem;
              padding-right: 1rem;
              padding-left: 1rem;
              padding-bottom: 5rem;
        }}  
    </style>
    """,
        unsafe_allow_html=True,
    )

    nltk.download("stopwords")
    nltk.download("punkt")
    stopwords = nltk.corpus.stopwords.words("english")
    wordcloud = get_wordcloud(stopwords=stopwords)
    st.pyplot(wordcloud)
    selected_state = draw_state_counties()
    state_wordcloud = get_wordcloud(STATE_TO_CODE_MAP[selected_state.strip()], stopwords)
    st.pyplot(state_wordcloud)
    draw_embedded_tweets(STATE_TO_CODE_MAP[selected_state.strip()])


if __name__ == "__main__":
    main()
