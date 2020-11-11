import matplotlib.pyplot as plt
import streamlit as st

import twitter.word_cloud

DATA_DIR = "data"


def draw_wordcloud():
    wc = twitter.word_cloud.main(DATA_DIR)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)


def main():
    draw_wordcloud()


if __name__ == "__main__":
    main()
