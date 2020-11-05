# Final Project Proposal

**Project URL**: TODO

## Fact-Checking Popular Opinions about COVID-19

Project Track: Narrative

Team members: Joseph Koshakow, Vivian Lee, James Mahler, Bradley Warren

### Defining the Problem

Despite the promises that technologies like the World Wide Web and social media platforms put forth to build community, bring people closer together, and enable the free exchange of ideas, our society today is more polarized than ever before. Though we can virtually move beyond our physical boundaries to meet and communicate with others around the globe, we still find ourselves hovering within the comfort of our individual social bubbles, where our nearest neighbors share our beliefs and values. Along with the development of online groups, forums, and algorithms tailored to our search preferences, this behavior has a direct influence on the information we learn and beliefs we develop about certain topics.

COVID-19 is no exception. In the past few months, we’ve been bombarded with a wide array of conflicting opinions, including but not limited to: how effective wearing a mask is, whether coronavirus is airborne, what impact the virus has on people in certain age ranges, and what the virus reveals about underlying societal issues like socioeconomic and education divides in our country.

For this project, we plan to analyze COVID-19 data collected from the CMU Delphi Research Group’s COVIDcast Epidata API to build a narrative around fact-checking popular opinions about COVID-19. We seek to investigate commonly-held beliefs and provide data-driven answers that will support or debunk them.

Examples of topics and questions within them that we intend to explore are:

1. Impact of socioeconomic class (geographic location) on COVID-related deaths
    - Are there more COVID-related deaths among residents of poor counties compared to wealthy counties?

2. Impact of education level on following COVID health precautions
    - Do people in more educated counties really wear masks more often than people in less educated counties?
    
3. Comparing US response to pandemic with other countries
    - Was the US response to the pandemic really worse than other countries or did the other countries under-report COVID cases? (covid-related deaths vs deaths by any cause)
    
4. Impact of students returning to campus on their college towns
    - Did college towns with universities that opened their campuses for the Fall semester experience spikes in reported COVID cases, symptoms, or deaths after students returned for the fall semester?
    
5. Explore the impact of different states having in person vs remote classes
    - Potential impact in cases or public sentiment
    
### Analyzing Tweets

We are planning to analyze twitter data on the coronavirus to help further guide our analysis on popular beliefs about the virus. We want to feed coronavirus related tweets into a Latent Dirichlet Allocation (LDA) model, and hope this will allow us to extract meaningful subtopics. From there we can see which topics have the most tweets and what people’s beliefs are related to those topics. Using our datasets we’ll attempt to show whether or not these sentiments from twitter are supported by data or not.

### Datasets to Use
- [CMU COVIDcast Epidata API](https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html) ([data](https://covidcast.cmu.edu/?sensor=doctor-visits-smoothed_adj_cli&level=county&date=20201030&signalType=value&encoding=color&mode=export&region=42003))
- US Department of Agriculture county-level data sets ([all](https://www.ers.usda.gov/data-products/county-level-data-sets/), [poverty](https://data.ers.usda.gov/reports.aspx?ID=17826), [population](https://data.ers.usda.gov/reports.aspx?ID=17827), [unemployment rate and median household income](https://data.ers.usda.gov/reports.aspx?ID=17828), [education](https://data.ers.usda.gov/reports.aspx?ID=17829))
- World Bank Education ([COVID-19 school closures map](https://www.worldbank.org/en/data/interactive/2020/03/24/world-bank-education-and-covid-19), [global education stats](https://databank.worldbank.org/source/education-statistics-%5e-all-indicators))
- John Hopkins ([COVID dataset](https://github.com/CSSEGISandData/COVID-19))
- Twitter ([tweets dataset](https://tweetsets.library.gwu.edu/datasets))

### Proposed Deliverable

After analyzing the data, we plan to present a narrative in the form of a narrative article. We plan to create this narrative using Streamlit in Python, although we are open to using other technologies as well. Using Streamlit will also allow us to have our narrative article be interactive if we so choose. One of the biggest initial tasks for us will be to come up with a narrative, which will be done by analyzing and exploring the questions listed above.
