import os
from datetime import timedelta
from math import ceil, floor

import altair as alt
import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from vega_datasets import data

import twitter.tweet_fetcher
import twitter.word_cloud
from twitter.state_data_aggregator import STATE_TO_CODE_MAP
from twitter.tweet_fetcher import get_saved_tweet_oembeds

DATA_DIR = "data"
alt.data_transformers.disable_max_rows()


@st.cache(allow_output_mutation=True)  # add caching so we load the data only once
def load_state_fips():
    state_fips = pd.read_csv("data/fips/clean/state_fips_2019.csv", index_col=0)
    state_fips = state_fips[state_fips["State FIPS"] > 0]  # exclude regions, divisions, and non-state rows
    return state_fips[["State FIPS", "Name"]].sort_values("Name").set_index("Name").to_dict()["State FIPS"]


@st.cache(allow_output_mutation=True)
def load_county_fips():
    county_fips = pd.read_csv("data/fips/clean/county_fips_2019.csv", index_col=0)
    return county_fips[["State FIPS", "FIPS", "Area Name"]]


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


def read_and_filter_df(df_name, cumulative=False):
    # Read in data from local csv file
    df = pd.read_csv(f"data/covidcast/clean/{df_name}.csv", index_col=0)

    # Remove rows with values < 0.0 (not possible)
    df = df[df['value'] >= 0.0]

    # Convert time_value column into datetime type
    df['time_value'] = pd.to_datetime(df['time_value'])

    # Only fetch most recent cumulative data
    if cumulative:
        df = df.sort_values('time_value')
        df = df[~df.duplicated('FIPS', keep='last')]

    return df


@st.cache(allow_output_mutation=True)
def load_covid_data():
    covid_data = {}
    covid_df_names = {
        'Cumulative Cases per 100K people': "confirmed_cumulative_cases_prop_fips",
        'Daily New Cases per 100K people': "confirmed_daily_incidence_cases_prop_fips",
        "Cumulative Deaths per 100K people": "cumulative_deaths_prop_fips",
        "Daily Deaths per 100K people": "daily_incidence_deaths_prop_fips",
        "Daily % Covid-Related Doctor Visits": "perc_covid_doctor_visits_fips",
        "% People Wearing Masks in Public in Past 5 Days": "perc_people_wearing_masks_fips",
        "% People Tested for Covid in Past 14 Days": "perc_people_tested_fips",
        "% Positive Covid Tests in Past 14 Days": "perc_positive_tests_fips",
        "% People not Tested who Wanted Tests": "perc_wanted_test_fips"
    }
    for covid_feature_name, covid_df_name in covid_df_names.items():
        cumulative = "cumulative" in covid_feature_name.lower()
        covid_data[covid_feature_name] = read_and_filter_df(covid_df_name, cumulative)
    return covid_data


@st.cache(allow_output_mutation=True)
def get_covid_date_ranges(covid_data):
    covid_date_ranges = {}
    for covid_feature, df in covid_data.items():
        covid_date_ranges[covid_feature] = df["time_value"].min(), df["time_value"].max()
    return covid_date_ranges


STATE_FIPS_DICT = load_state_fips()
COUNTY_FIPS_DF = load_county_fips()  # {State FIPS, FIPS, Area Name}
STATES = list(STATE_FIPS_DICT.keys())
USDA_DATA = load_usda_data()
COVID_DATA = load_covid_data()
COVID_DATE_RANGES = get_covid_date_ranges(COVID_DATA)


@st.cache(allow_output_mutation=True)
def get_cleaned_tweet_words(state=None, stopwords=None):
    return twitter.word_cloud.get_cleaned_tweet_words(DATA_DIR, state, stopwords)


@st.cache(allow_output_mutation=True)
def get_wordcloud(tweets, state=None):
    wc = twitter.word_cloud.get_wordcloud(tweets, DATA_DIR, state)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    return fig


@st.cache(allow_output_mutation=True)
def get_wordcloud_from_file(state=None):
    file_name = state if state else "World"
    file_path = f"data/word_clouds/{file_name}.jpg"
    if os.path.exists(file_path):
        return Image.open(file_path)
    else:
        return None


@st.cache(allow_output_mutation=True)
def get_word_df(words):
    df = pd.DataFrame({"word": words})
    df = df.groupby("word").size().to_frame()
    df.reset_index(inplace=True)
    df.rename(columns={df.columns[1]: "count"}, inplace=True)
    df.sort_values("count", ascending=False, inplace=True)
    return df


def draw_tweet_data(stopwords, representation, container, state=None):

    container.subheader("Most Frequent Words")
    container.info("Use the radio buttons on the sidebar to toggle between word cloud and bar chart views")

    if representation == "Word Cloud":
        cached_pic = get_wordcloud_from_file(state)
        if cached_pic:
            # Here we scale the width to obtain a constant height
            width, height = cached_pic.size
            desired_height = 600
            mult = desired_height/height
            cached_pic = cached_pic.resize((int(width*mult), desired_height))

            container.image(cached_pic)
        else:
            cleaned_tweets = get_cleaned_tweet_words(state, stopwords)
            wordcloud = get_wordcloud(cleaned_tweets, state)
            container.pyplot(wordcloud)
    else:
        cleaned_tweets = get_cleaned_tweet_words(state, stopwords)
        title = f"{state} Tweets" if state else "Global Tweets"
        bar_chart_size = 50
        df = get_word_df(cleaned_tweets).head(bar_chart_size)
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("word:N", sort="-y"),
            y=alt.Y("count:Q"),

        ).properties(title=title)
        container.write(chart)


def get_state_map_base(counties, selected_state_fips):
    base = alt.Chart(data=counties)\
        .mark_geoshape(stroke='black', strokeWidth=1)\
        .transform_calculate(state_id="(datum.id/1000)|0", FIPS="datum.id")\
        .transform_filter(alt.datum.state_id == selected_state_fips)\
        .properties(width=400, height=400)

    # Use albersUsa map for Alaska to fix zoom issue
    if selected_state_fips == 2:
        base = base.project(type='albersUsa')

    return base


def add_selection(map, highlighter, multiselector):
    return map.add_selection(highlighter, multiselector) \
        .encode(stroke=alt.condition(highlighter | multiselector, alt.value('purple'), alt.value('black')),
                strokeWidth=alt.condition(highlighter | multiselector, alt.StrokeWidthValue(2.2),
                                          alt.StrokeWidthValue(1.0)))


def get_specific_state_map(state_map_base, selected_feature, selected_feature_label, lookup_df, lookup_fields):
    return state_map_base.encode(color="%s:Q" % selected_feature,
                                 tooltip=[alt.Tooltip('id:N', title='FIPS'),
                                          alt.Tooltip('Area Name:N', title='Location'),
                                          alt.Tooltip('%s:Q' % selected_feature, title=selected_feature_label)]) \
        .transform_lookup(lookup='id', from_=alt.LookupData(lookup_df, 'FIPS', [selected_feature] + lookup_fields))


def round_to_nearest(number, nearest, roundup=True):
    return int(ceil(number / nearest) * nearest) if roundup else int(floor(number / nearest) * nearest)


def get_covid_corr_chart(full_df, selected_usda_feature, selected_covid_feature):
    correlation = np.corrcoef(full_df["value"], full_df[selected_usda_feature])

    x_min = round_to_nearest(full_df['value'].min(), 10, roundup=False)
    x_max = round_to_nearest(full_df['value'].max(), 10, roundup=True)
    y_min = round_to_nearest(full_df[selected_usda_feature].min(), 10, roundup=False)
    y_max = round_to_nearest(full_df[selected_usda_feature].max(), 10, roundup=True)

    covid_details_chart = alt.Chart(full_df).mark_point() \
        .encode(x=alt.X("value:Q",
                        axis=alt.Axis(title=selected_covid_feature),
                        scale=alt.Scale(domain=[x_min, x_max])),
                y=alt.Y(selected_usda_feature + ":Q",
                        scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=[alt.Tooltip("Area Name_x:N", title="County")]) \
        .properties(title="Correlation between %s and %s: %.4f" % (
        selected_covid_feature, selected_usda_feature, correlation[0, 1]))

    covid_details_chart = covid_details_chart + \
                          covid_details_chart\
                              .transform_regression('value', selected_usda_feature, method='linear') \
                              .mark_line(color="#000000")
    return covid_details_chart


def widget_key(widget_name, selected_state_fips=None):
    return widget_name if selected_state_fips is None else f"{widget_name}_state"


def draw_control_panel(col1, col2, container, selected_state_fips=None):

    # Select USDA socioeconomic indicator
    selected_usda_category = col1.selectbox('Socioeconomic Indicator', options=list(USDA_DATA.keys()), index=0,
                                            key=widget_key("usda_category", selected_state_fips))
    usda_df = USDA_DATA.get(selected_usda_category)
    usda_df = usda_df[usda_df["FIPS"] % 1000 != 0]  # remove non-county rows

    # Select USDA feature to color choropleth map
    usda_features = [col for col in usda_df.columns if col not in ['FIPS', 'State Abrv', 'Area Name']]
    selected_usda_feature = col1.selectbox('Measure', options=usda_features, index=0,
                                           key=widget_key("usda_feature", selected_state_fips))

    # Select Covid-19 feature to color choropleth map
    selected_covid_feature = col2.selectbox('Covid-19 Feature', options=list(COVID_DATA.keys()), index=0,
                                            key=widget_key("covid_feature", selected_state_fips))
    covid_df = COVID_DATA.get(selected_covid_feature)

    selected_covid_agg_function = None
    covid_df_agg = None

    # Filter for counties in the selected state
    if selected_state_fips is not None:
        usda_df = usda_df[usda_df["FIPS"] // 1000 == selected_state_fips]
        covid_df = covid_df[covid_df["FIPS"] // 1000 == selected_state_fips]

    if 'Cumulative' not in selected_covid_feature:

        # Select date range
        min_date, max_date = COVID_DATE_RANGES.get(selected_covid_feature)
        selected_min_date = col2.date_input("From Date", value=max_date - timedelta(days=7),
                                            min_value=min_date, max_value=max_date,
                                            key=widget_key("min_date", selected_state_fips))
        selected_max_date = col2.date_input("To Date", value=max_date,
                                            min_value=selected_min_date, max_value=max_date,
                                            key=widget_key("max_date", selected_state_fips))
        if selected_min_date > selected_max_date:
            container.error("ERROR: 'From Date' must be earlier or equal to 'To Date'")

        # Select function for values in date range
        covid_date_range_functions = ["Max", "Min", "Average", "Median"]
        selected_covid_agg_function = col2.selectbox("Statistic for date range", options=covid_date_range_functions,
                                                     index=covid_date_range_functions.index("Max"),
                                                     key=widget_key("covid_agg_function", selected_state_fips))

        # Select rows within date range
        covid_df = covid_df[(covid_df["time_value"] >= pd.Timestamp(selected_min_date)) &
                            (covid_df["time_value"] <= pd.Timestamp(selected_max_date))]

        # Aggregate data based on selected agg function
        covid_df_agg = covid_df.groupby(['FIPS', 'Area Name'])['value']\
            .agg(Min='min', Max='max', Average='mean', Median='median') \
            .reset_index()

    else:
        col2.selectbox('Cumulative as of', options=[COVID_DATE_RANGES.get(selected_covid_feature)[1].strftime("%B %d, %Y")],
                       key=widget_key("cumulative_last_update", selected_state_fips))

    control_panel = {
        'usda_df': usda_df,
        'covid_df': covid_df,
        'covid_df_agg': covid_df_agg,
        'selected_usda_category': selected_usda_category,
        'selected_usda_feature': selected_usda_feature,
        'selected_covid_feature': selected_covid_feature,
        'selected_covid_agg_function': selected_covid_agg_function
    }

    return control_panel


def draw_us_counties(container):

    counties = alt.topo_feature(data.us_10m.url, 'counties')
    col1, col2 = container.beta_columns(2)
    control_panel = draw_control_panel(col1, col2, container, selected_state_fips=None)

    # TODO Commented lines are for being able to select counties on the map, didn't finish it yet
    #country_highlight = alt.selection_single(on='mouseover', empty=empty, fields=["FIPS"])
    #country_multiselect = alt.selection_multi(empty=empty, fields=["FIPS"])

    country_base = alt.Chart(counties)\
        .mark_geoshape(stroke='black', strokeWidth=1) \
        .transform_calculate(state_id="(datum.id/1000)|0", FIPS="datum.id") \
        .properties(width=850, height=500) \
        .project(type="albersUsa")
        # .add_selection(country_highlight, country_multiselect) \

    usa_map_background = alt.Chart(data=counties)\
        .mark_geoshape(stroke='black', strokeWidth=1, fill='lightgray')\
        .transform_filter(alt.datum.id % 1000 != 0)\
        .properties(width=850, height=500)\
        .project(type="albersUsa")

    usda_usa_map = get_specific_state_map(country_base,
                                          selected_feature=control_panel.get('selected_usda_feature'),
                                          selected_feature_label='Value',
                                          lookup_df=control_panel.get('usda_df'),
                                          lookup_fields=['Area Name'])
    usda_usa_map = usda_usa_map\
        .properties(title="%s: %s" % (control_panel.get('selected_usda_category'), control_panel.get('selected_usda_feature')))

    container.write(alt.layer(usa_map_background, usda_usa_map).configure_legend(orient='bottom'))

    if 'Cumulative' not in control_panel.get('selected_covid_feature'):

        covid_usa_map = get_specific_state_map(country_base,
                                               selected_feature=control_panel.get('selected_covid_agg_function'),
                                               selected_feature_label=control_panel.get('selected_covid_agg_function'),
                                               lookup_df=control_panel.get('covid_df_agg'),
                                               lookup_fields=['time_value', 'issue', 'Area Name'])

        covid_usa_map = covid_usa_map.properties(title=control_panel.get('selected_covid_feature'))
        container.write(alt.layer(usa_map_background, covid_usa_map).configure_legend(orient='bottom'))

    else:
        covid_usa_map = get_specific_state_map(country_base,
                                               selected_feature='value',
                                               selected_feature_label='Value',
                                               lookup_df=control_panel.get('covid_df'),
                                               lookup_fields=['time_value', 'issue', 'Area Name'])
        covid_usa_map = covid_usa_map.properties(title=control_panel.get('selected_covid_feature'))

        full_df_usa = control_panel.get('covid_df').merge(control_panel.get('usda_df'), on="FIPS")
        usa_cor_plot = get_covid_corr_chart(full_df_usa, control_panel.get('selected_usda_feature'),
                                            control_panel.get('selected_covid_feature'))
        usa_cor_plot = usa_cor_plot.properties(width=800, height=500)

        container.write(alt.layer(usa_map_background, covid_usa_map).configure_legend(orient='bottom'))
        container.write(usa_cor_plot)


def draw_state_counties(selected_state, container):

    counties = alt.topo_feature(data.us_10m.url, 'counties')
    selected_state_fips = STATE_FIPS_DICT.get(selected_state)
    col1, col2 = container.beta_columns(2)

    control_panel = draw_control_panel(col1, col2, container, selected_state_fips)
    container.info('Hold Shift + click counties to only see their data on the chart below. Double-click map to reset selection.')

    select_all_counties_default = not ('Cumulative' not in control_panel.get('selected_covid_feature'))
    select_all_counties = "all" if container.checkbox('Select all counties by default to display on plot', value=select_all_counties_default) else "none"
    county_highlight = alt.selection_single(on='mouseover', empty=select_all_counties, fields=["FIPS"])
    county_multiselect = alt.selection_multi(empty=select_all_counties, fields=["FIPS"])

    # Get state map base
    state_map_base = get_state_map_base(counties, selected_state_fips)

    # Create county socioeconomic indicator map
    usda_state_map = get_specific_state_map(state_map_base,
                                            selected_feature=control_panel.get('selected_usda_feature'),
                                            selected_feature_label='Value',
                                            lookup_df=control_panel.get('usda_df'), lookup_fields=['Area Name'])

    usda_state_map = add_selection(usda_state_map, county_highlight, county_multiselect) \
        .properties(title="%s: %s" % (control_panel.get('selected_usda_category'), control_panel.get('selected_usda_feature')))

    if 'Cumulative' not in control_panel.get('selected_covid_feature'):
        covid_state_map = get_specific_state_map(state_map_base,
                                                 selected_feature=control_panel.get('selected_covid_agg_function'),
                                                 selected_feature_label=control_panel.get('selected_covid_agg_function'),
                                                 lookup_df=control_panel.get('covid_df_agg'),
                                                 lookup_fields=['time_value', 'issue', 'Area Name'])
        covid_state_map = covid_state_map.properties(title=control_panel.get('selected_covid_feature'))

        x_min = control_panel.get('covid_df')['time_value'].min()
        x_max = control_panel.get('covid_df')['time_value'].max()
        y_min = round_to_nearest(control_panel.get('covid_df')['value'].min(), 10, roundup=False)
        y_max = round_to_nearest(control_panel.get('covid_df')['value'].max(), 10, roundup=True)

        covid_details_chart = alt.Chart(control_panel.get('covid_df')).mark_line() \
            .encode(x=alt.X('time_value:T', axis=alt.Axis(title="Day", format=("%b %d, %Y"), labelAngle=-45),
                            scale=alt.Scale(domain=[x_min, x_max])),
                    y=alt.Y('value:Q', axis=alt.Axis(title="%s" % control_panel.get('selected_covid_feature')),
                            scale=alt.Scale(domain=[y_min, y_max])),
                    color=alt.Color("Area Name"),
                    tooltip=[alt.Tooltip('Area Name:N', title="County")]) \
            .properties(title="Time Series Analysis for %s" % control_panel.get('selected_covid_feature')) \
            .add_selection(county_multiselect) \
            .transform_filter(county_multiselect)
    else:
        covid_state_map = get_specific_state_map(state_map_base,
                                                 selected_feature='value',
                                                 selected_feature_label='Value',
                                                 lookup_df=control_panel.get('covid_df'),
                                                 lookup_fields=['time_value', 'issue', 'Area Name'])
        covid_state_map = covid_state_map.properties(title=control_panel.get('selected_covid_feature'))

        # Find correlation between the feature and the COVID stats
        full_df = control_panel.get('covid_df').merge(control_panel.get('usda_df'), on="FIPS")
        covid_details_chart = get_covid_corr_chart(full_df,
                                                   control_panel.get('selected_usda_feature'),
                                                   control_panel.get('selected_covid_feature'))
        covid_details_chart = covid_details_chart \
            .add_selection(county_multiselect) \
            .transform_filter(county_multiselect)

    # Draw maps side-by-side
    map_background = alt.Chart(data=counties)\
        .mark_geoshape(stroke='black', strokeWidth=1, fill='lightgray')\
        .transform_calculate(state_id="(datum.id/1000)|0", FIPS="datum.id")\
        .transform_filter((alt.datum.state_id == selected_state_fips) & (alt.datum.id % 1000 != 0))\
        .properties(width=400, height=400)\
        .encode(tooltip=[alt.Tooltip('id:N', title='FIPS'),
                         alt.Tooltip('Area Name:N', title='Location')])\
        .transform_lookup(lookup='id', from_=alt.LookupData(COUNTY_FIPS_DF, 'FIPS', ['Area Name']))

    covid_state_map = add_selection(alt.layer(map_background, covid_state_map), county_highlight, county_multiselect)
    state_maps = alt.hconcat(usda_state_map, covid_state_map).resolve_scale(color='independent')

    # Draw covid details chart below maps
    covid_details_chart = covid_details_chart.properties(width=800, height=400)
    container.write(alt.vconcat(state_maps, covid_details_chart).configure_legend(orient='bottom'))


def draw_embedded_tweets(state, container):
    tweet_oembeds = get_saved_tweet_oembeds(DATA_DIR, state)
    num_tweets = len(tweet_oembeds)
    half_num = int(num_tweets / 2)
    # Two rows are good for now with 6 tweets
    container.subheader("Example Tweets")
    row1 = container.beta_columns(half_num) if half_num > 0 else []
    row2 = container.beta_columns(num_tweets - half_num) if num_tweets - half_num > 0 else []
    for i in range(num_tweets):
        if i < half_num:
            row1[i].markdown(tweet_oembeds[i], unsafe_allow_html=True)
            # with row1[i]:
            #     container.markdown(tweet_oembeds[i], unsafe_allow_html=True)
        else:
            row2[i-half_num].markdown(tweet_oembeds[i], unsafe_allow_html=True)
            # with row2[i - half_num]:
            #     container.markdown(tweet_oembeds[i], unsafe_allow_html=True)


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

    # Import package data
    nltk.download("stopwords")
    nltk.download("punkt")
    stopwords = nltk.corpus.stopwords.words("english")

    # Page Title
    st.title("US Socioeconomic Indicators vs Covid-19")

    # Sidebar
    word_rep = st.sidebar.radio("Display tweets as: ", ("Word Cloud", "Bar Chart"))
    selected_state = st.sidebar.selectbox('US State', options=STATES, index=STATES.index("Pennsylvania"))

    # Container Objects
    state_tweets_container = st.beta_expander(f"{selected_state} Tweets", expanded=True)
    state_indicators_container = st.beta_expander(f"{selected_state} Indicators", expanded=True)
    global_tweets_container = st.beta_expander("Global Tweets")
    country_indicators_container = st.beta_expander("United States Indicators")

    # State Tweets
    state_code = STATE_TO_CODE_MAP[selected_state.strip()]
    draw_tweet_data(stopwords, word_rep, state_tweets_container, state_code)
    draw_embedded_tweets(STATE_TO_CODE_MAP[selected_state.strip()], container=state_tweets_container)

    # State Indicators
    draw_state_counties(selected_state, state_indicators_container)

    # Global Tweets
    draw_tweet_data(stopwords, word_rep, global_tweets_container, None)

    # United States Indicators
    draw_us_counties(country_indicators_container)


if __name__ == "__main__":
    main()
