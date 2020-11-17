import os
import random
import time

# http://docs.tweepy.org/en/latest/index.html
import tweepy

from twitter.state_data_aggregator import STATE_TO_CODE_MAP
from twitter.twitter_secret_fetcher import get_api_key, get_api_secret_key, get_access_token, get_access_token_secret

# Percentage of COVID tweets to sample, there are 239,861,658 in total and roughly 2,000,000 with geo tags
SAMPLE_PERCENTAGE = 1
# Directory containing files that have COVID tweet IDs
# I left this out of the git repo because it takes a LONG time to push and pull. So if you want to run this, just
# download it your self and place them in this directory
COVID_TWEET_ID_DIR = "../data/tweets/covid_tweet_ids"
# COVID Tweet IDs with geo information
GEO_COVID_TWEET_IDS = "../data/tweets/geo_covid_tweet_ids"
# Directory containing files that have COVID tweet text
COVID_TWEET_TEXT_DIR = "../data/tweets/covid_tweets"
# Directory containing files that have COVID tweet text by state
GEO_COVID_TWEET_TEXT_DIR = "../data/tweets/geo_covid_tweets"


###############################################
# Sample Tweet Ids From File
###############################################

# Tweet IDs come from here: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LW0BTB
# More Twitter Data: https://tweetsets.library.gwu.edu/dataset/369433fd
def sample_tweet_ids(use_geo_tweets=False):
    sampled_ids = []
    directory = GEO_COVID_TWEET_IDS if use_geo_tweets else COVID_TWEET_ID_DIR
    for file_name in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file_name)):
            sampled_ids.extend(sample_tweet_ids_from_file(directory, file_name))
    return sampled_ids


def sample_tweet_ids_from_file(directory, file_name):
    # We have to read through every line which could be time consuming. If this becomes a bottleneck look into algo #3
    # from here: http://metadatascience.com/2014/02/27/random-sampling-from-very-large-files/ or some other faster algo
    sampled_ids = []
    with open(f"{directory}/{file_name}") as f:
        for tweet_id in f.readlines():
            if should_sample():
                sampled_ids.append(int(tweet_id.strip()))
    print(f"Sampled {file_name}")
    return sampled_ids


def should_sample():
    if SAMPLE_PERCENTAGE == 1:
        return True
    # Since we're going to limit to english tweets, we'll make the naive assumption that half of the tweets are english
    return random.random() < SAMPLE_PERCENTAGE * 2


###############################################
# Get Tweets From Twitter API
###############################################

def connect_to_twitter():
    auth = tweepy.OAuthHandler(get_api_key(), get_api_secret_key())
    auth.set_access_token(get_access_token(), get_access_token_secret())
    return tweepy.API(auth)


def get_tweets_by_state(api):
    for state, state_code in STATE_TO_CODE_MAP.items():
        if os.path.exists(f"{GEO_COVID_TWEET_IDS}/geo/{state_code}.txt"):
            with open(f"{GEO_COVID_TWEET_IDS}/geo/{state_code}.txt") as f:
                tweet_ids = [tweet_id.strip() for tweet_id in f.readlines()]
                print(f"Fetching tweets for {state}")
                get_tweets(tweet_ids, api, True, state_code)
                print(f"Done fetching tweets for {state}")


def get_tweets(tweet_ids, api, use_geo_data=False, state=None):
    i = 0
    # Can only fetch tweets in batches of 100
    while i < len(tweet_ids):
        # Super hacky I know
        try:
            tweets = api.statuses_lookup(tweet_ids[i:i + 100], include_entities=True, tweet_mode='extended')
        except tweepy.RateLimitError:
            # In case we hit the rate limit wait 15 minutes and try again
            # https://developer.twitter.com/en/docs/twitter-api/v1/rate-limits
            time.sleep(15 * 60)
            try:
                tweets = api.statuses_lookup(tweet_ids[i:i + 100], include_entities=True, tweet_mode='extended')
            except tweepy.error.TweepError:
                pass
        except tweepy.error.TweepError:
            try:
                tweets = api.statuses_lookup(tweet_ids[i:i + 100], include_entities=True, tweet_mode='extended')
            except:
                pass

        if use_geo_data:
            clean_and_flush_with_geo(tweets, state)
        else:
            clean_and_flush_without_geo(tweets)
        i += 100
        print(f"finished tweet batch {int(i / 100)}")


def clean_and_flush_with_geo(tweets, state=None):
    tweets_by_state = {}
    filtered_tweets = [tweet for tweet in tweets if
                       tweet.lang == 'en' and tweet.place and tweet.place.country_code == 'US']
    for tweet in filtered_tweets:

        if state is None:
            state = get_state_from_tweet(tweet)
        if state:
            if state in tweets_by_state:
                tweets_by_state[state].append(tweet)
            else:
                tweets_by_state[state] = [tweet]

    for state, tweets in tweets_by_state.items():
        tweet_ids = [tweet.id for tweet in tweets]
        flush_list(tweet_ids, f"{GEO_COVID_TWEET_IDS}/geo/{state}.txt")
        tweet_texts = [clean_tweet(tweet) for tweet in tweets]
        flush_list(tweet_texts, f"{GEO_COVID_TWEET_TEXT_DIR}/{state}.txt")


def get_state_from_tweet(tweet):
    if tweet.place.place_type == "admin":
        return tweet.place.full_name.split(',')[0].strip()
    else:
        state = tweet.place.full_name.split(',')[-1].strip()
        if len(state) != 2:
            print(f"full name: {tweet.place.full_name}; place type: {tweet.place.place_type}")
            return None
        return state


def clean_and_flush_without_geo(tweets):
    # We add the timestamp to the file name as a unique identifier so we don't overwrite older files
    ts = time.time()
    file_name = f"{COVID_TWEET_TEXT_DIR}/tweets_{ts}.txt"
    # Limit to english tweets
    tweet_text = [clean_tweet(tweet) for tweet in tweets if tweet.lang == 'en']
    flush_list(tweet_text, file_name)


def clean_tweet(tweet):
    tweet_text = tweet.full_text
    if tweet_text is None and tweet.retweeted_status:
        tweet_text = tweet.retweeted_status.full_text
    if tweet_text is None:
        tweet_text = tweet.text
    if tweet_text is None:
        return ""
    # Remove new lines from tweet so tweet fits on a single line
    # TODO consider removing mentions
    return tweet_text.replace('\n', '').replace('\r', '')


def flush_list(list_, file_name):
    with open(file_name, "a+") as f:
        f.writelines(f"{tweet}\n" for tweet in list_)


def get_html():
    api = connect_to_twitter()
    res = api.get_oembed(1248540485733552128)
    return res["html"]


def main():
    # use_geo_location = True
    # sampled_tweet_ids = sample_tweet_ids(use_geo_location)
    api = connect_to_twitter()
    get_tweets_by_state(api)
    # get_tweets(sampled_tweet_ids, api, use_geo_location, None)


if __name__ == "__main__":
    main()
