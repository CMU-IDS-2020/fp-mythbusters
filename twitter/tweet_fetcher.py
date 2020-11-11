import os
import random
import time

# http://docs.tweepy.org/en/latest/index.html
import tweepy

from twitter.twitter_secret_fetcher import get_api_key, get_api_secret_key, get_access_token, get_access_token_secret

# Percentage of COVID tweets to sample, there are 239,861,658 in total
SAMPLE_PERCENTAGE = 0.0001
# Directory containing files that have COVID tweet IDs
# I left this out of the git repo because it takes a LONG time to push and pull. So if you want to run this, just
# download it your self and place them in this directory
COVID_TWEET_ID_DIR = "../data/covid_tweet_ids"
# Directory containing files that have COVID tweet text
COVID_TWEET_TEXT_DIR = "../data/covid_tweets"


###############################################
# Sample Tweet Ids From File
###############################################

# Tweet IDs come from here: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LW0BTB
def sample_tweet_ids():
    sampled_ids = []
    for file_name in os.listdir(COVID_TWEET_ID_DIR):
        sampled_ids.extend(sample_tweet_ids_from_file(file_name))
    return sampled_ids


def sample_tweet_ids_from_file(file_name):
    # We have to read through every line which could be time consuming. If this becomes a bottleneck look into algo #3
    # from here: http://metadatascience.com/2014/02/27/random-sampling-from-very-large-files/ or some other faster algo
    sampled_ids = []
    with open(f"../data/covid_tweet_ids/{file_name}") as f:
        for tweet_id in f.readlines():
            if should_sample():
                sampled_ids.append(int(tweet_id.strip()))
    print(f"Sampled {file_name}")
    return sampled_ids


def should_sample():
    # Since we're going to limit to english tweets, we'll make the naive assumption that half of the tweets are english
    return random.random() < SAMPLE_PERCENTAGE * 2


###############################################
# Get Tweets From Twitter API
###############################################

def connect_to_twitter():
    auth = tweepy.OAuthHandler(get_api_key(), get_api_secret_key())
    auth.set_access_token(get_access_token(), get_access_token_secret())
    return tweepy.API(auth)


def get_tweets(tweet_ids, api):
    # We add the timestamp to the file name as a unique identifier so we don't overwrite older files
    ts = time.time()
    file_name = f"{COVID_TWEET_TEXT_DIR}/tweets_{ts}.txt"
    i = 0
    # Can only fetch tweets in batches of 100
    while i < len(tweet_ids):
        try:
            tweets = api.statuses_lookup(tweet_ids[i:i + 100])
        except tweepy.RateLimitError:
            # In case we hit the rate limit wait 15 minutes and try again
            # https://developer.twitter.com/en/docs/twitter-api/v1/rate-limits
            time.sleep(15 * 60)
            tweets = api.statuses_lookup(tweet_ids[i:i + 100])
        # Limit to english tweets
        tweet_text = [clean_tweet(tweet.text) for tweet in tweets if tweet.lang == 'en']
        i += 100
        flush_tweets(tweet_text, file_name)
        print(f"finished tweet batch {int(i / 100)}")


def clean_tweet(tweet):
    # Remove new lines from tweet so tweet fits on a single line
    return tweet.replace('\n', '').replace('\r', '')


def flush_tweets(tweets, file_name):
    with open(file_name, "a+") as f:
        f.writelines(f"{tweet}\n" for tweet in tweets)


def main():
    sampled_tweet_ids = sample_tweet_ids()
    api = connect_to_twitter()
    get_tweets(sampled_tweet_ids, api)


if __name__ == "__main__":
    main()
