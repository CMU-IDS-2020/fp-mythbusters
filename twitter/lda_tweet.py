# Heavily influenced by
# https://towardsdatascience.com/nlp-extracting-the-main-topics-from-your-dataset-using-lda-in-minutes-21486f5aa925

import gensim
import nltk

'''
This ended up not being very useful. We thought the output of an LDA model would be more human readable
but instead each topic is a list of words with weights. For example when running this on the 24,000 tweet
sample we got this as an output

    Topic: 0
    Words: 0.031*"coronavirus" + 0.020*"https" + 0.014*"trump" + 0.011*"covid" + 0.008*"presid" + 0.007*"china" + 0.007*"realdonaldtrump" + 0.005*"american" + 0.004*"million" + 0.003*"invinc"

    Topic: 1
    Words: 0.021*"covid" + 0.018*"https" + 0.011*"pour" + 0.009*"dan" + 0.006*"coronavirus" + 0.005*"conflits_fr" + 0.005*"masqu" + 0.005*"confin" + 0.005*"tout" + 0.004*"admit"

    Topic: 2
    Words: 0.028*"covid" + 0.027*"https" + 0.027*"para" + 0.024*"coronavirus" + 0.009*"caso" + 0.008*"todo" + 0.007*"prueba" + 0.007*"persona" + 0.006*"sobr" + 0.006*"primer"

    Topic: 3
    Words: 0.019*"https" + 0.017*"covid" + 0.006*"kkmputrajaya" + 0.005*"todo" + 0.005*"coronavirus" + 0.005*"días" + 0.005*"malaysia" + 0.005*"sobr" + 0.004*"edselsalvana" + 0.004*"alguien"

    Topic: 4
    Words: 0.018*"https" + 0.012*"distanc" + 0.009*"social" + 0.008*"coronavirus" + 0.008*"go" + 0.006*"spend" + 0.006*"move" + 0.005*"stay" + 0.005*"strangeharbor" + 0.005*"surgica"

    Topic: 5
    Words: 0.017*"covid" + 0.013*"caso" + 0.010*"equip" + 0.009*"coronavirus" + 0.007*"president" + 0.007*"confirmado" + 0.006*"person" + 0.005*"poco" + 0.004*"arou" + 0.004*"silv"

    Topic: 6
    Words: 0.051*"covid" + 0.051*"https" + 0.025*"coronavirus" + 0.013*"peopl" + 0.007*"pandem" + 0.006*"time" + 0.006*"like" + 0.005*"help" + 0.005*"health" + 0.005*"need"

    Topic: 7
    Words: 0.030*"covid" + 0.027*"case" + 0.023*"coronavirus" + 0.020*"https" + 0.017*"test" + 0.011*"death" + 0.011*"report" + 0.008*"total" + 0.007*"number" + 0.007*"peopl"

    Topic: 8
    Words: 0.022*"coronavirus" + 0.019*"https" + 0.015*"covid" + 0.009*"conflits_fr" + 0.006*"franc" + 0.005*"mort" + 0.005*"plus" + 0.004*"sono" + 0.004*"prescrib" + 0.004*"plaquenil"

    Topic: 9
    Words: 0.008*"pelo" + 0.005*"moron" + 0.004*"llama" + 0.004*"minor" + 0.004*"scientifiqu" + 0.004*"avait" + 0.004*"https" + 0.004*"tota" + 0.004*"aplicación" + 0.003*"sake"

Most of them have "https" in them, so removing links probably would help. However even still this doesn't do a really
good job of telling us what people's sentiments are about COVID. 

I'm leaving the code here for historic/discussion purposes 
'''

# File containing tweets
TWEET_FILE = "../data/tweets/covid_tweets/tweets_24_000.txt"
stemmer = nltk.stem.SnowballStemmer("english")


def clean_tweet(tweet):
    # TODO probably not great to reinitialize each obj
    tokens = gensim.utils.simple_preprocess(tweet)
    tokens = [token for token in tokens if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3]
    tokens = [nltk.WordNetLemmatizer().lemmatize(token, pos='v') for token in tokens]
    tokens = [stemmer.stem(token) for token in tokens]
    return tokens


def clean_tweets(tweets):
    return [clean_tweet(tweet) for tweet in tweets]


def get_tweets():
    with open(TWEET_FILE) as f:
        return f.readlines()


def run_lda(tweets):
    dictionary = gensim.corpora.Dictionary(tweets)
    bows = [dictionary.doc2bow(tweet) for tweet in tweets]
    lda_model = gensim.models.LdaMulticore(bows, num_topics=10, id2word=dictionary, passes=10, workers=2)
    for idx, topic in lda_model.print_topics(-1):
        print(f"Topic: {idx} \nWords: {topic}\n")


def main():
    tweets = get_tweets()
    tweets = clean_tweets(tweets)
    run_lda(tweets)


if __name__ == "__main__":
    main()
