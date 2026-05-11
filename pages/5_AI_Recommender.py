import streamlit as st
from recommender import recommend_by_description
from recommender import load_data

st.title("🤖 AI Movie Recommender")

movies = load_data(
    r"G:\My Drive\movies data set\tmdb_5000_movies.csv",
    r"G:\My Drive\credit data set\tmdb_5000_credits.csv"
)

user_input = st.text_area(
    "Describe the movie you want",
    key="ai_movie_input"
)

if st.button(
    "Recommend",
    key="ai_recommend_btn"
):

    results = recommend_by_description(
        user_input,
        movies
    )

    st.subheader("Recommended Movies")

    for _, movie in results.iterrows():

        st.write(movie['title'])