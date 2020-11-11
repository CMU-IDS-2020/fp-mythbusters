import re

import nltk
# https://amueller.github.io/word_cloud/index.html
import wordcloud
from nltk.stem.wordnet import WordNetLemmatizer

# File containing tweets
TWEET_FILE = "covid_tweets/english_tweets_24_000.txt"


def get_tweets(data_dir):
    with open(f"{data_dir}/{TWEET_FILE}") as f:
        return f.readlines()


def word_to_pos(word):
    pos = nltk.pos_tag([word])[0][1]

    if pos.startswith('J'):
        return 'a'

    if pos.startswith('V'):
        return 'v'

    if pos.startswith('R'):
        return 'r'

    return 'n'


def valid_token(token, stopwords):
    # Removes some invalid tokens. rt is for retweets, somehow http/https made it through the url remove, and words
    # that end in "..." are the end of a tweet and often partial words. We also remove covid and corona because those
    # are going to be the most dominant words, but they don't really tell us anything. We already know that these tweets
    # are about corona/covid
    return len(token) > 3 and token != "rt" and token != "http" and token != "https" \
           and not token.startswith("//t.co") and not token.endswith("...") and "corona" not in token \
           and "covid" not in token and token not in stopwords


def clean_tweet(tweet, lemmatizer, stopwords):
    # (Attempt to) Remove URLs
    url_pattern = re.compile(r'https?://.*?\.(com|org|net|edu|gov)')
    tweet = url_pattern.sub(lambda m: " ", tweet)
    tweet.replace("'", "")
    tweet = tweet.lower()

    tokens = nltk.word_tokenize(tweet)

    # The lemmatizer doesn't really give us any better results and it cause a pretty big performance hit. For now I'm
    # leaving it out, but we can add it back in later
    # tokens = [lemmatizer.lemmatize(token, pos=word_to_pos(token)) for token in tokens if valid_token(token, stopwords)]

    tokens = [token.strip() for token in tokens if valid_token(token.strip(), stopwords)]

    return tokens


def clean_tweets(tweets, lemmatizer, stopwords):
    return [clean_tweet(tweet, lemmatizer, stopwords) for tweet in tweets]


def flatten_list(list_of_lists):
    return [element for lst in list_of_lists for element in lst]


def create_wordcloud(tweets):
    flat_tweets = flatten_list(tweets)
    tweet_str = " ".join(flat_tweets)
    # TODO Consider saving this to a file with pickle so we don't have to recompute every time. Since the tweet files
    #  are static, then this should never change for the same tweet file.
    return wordcloud.WordCloud().generate(tweet_str)


def main(data_dir):
    lemmatizer = WordNetLemmatizer()
    stopwords = set(nltk.corpus.stopwords.words("english"))
    # In case we want to re-include spanish tweets
    # stopwords.union(nltk.corpus.stopwords.words("spanish"))
    tweets = get_tweets(data_dir)
    tweets = clean_tweets(tweets, lemmatizer, stopwords)
    return create_wordcloud(tweets)


if __name__ == "__main__":
    main("../data")
