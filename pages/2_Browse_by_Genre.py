"""
pages/2_Browse_by_Genre.py
Browse the catalogue filtered by genre.
"""

import streamlit as st

st.set_page_config(page_title="Browse by Genre | MOAZZIZ", page_icon="🗂️", layout="wide")

if "user" not in st.session_state:
    st.warning("🔒 Please log in first.")
    if st.button("← Go to Login", key="login_redirect"):
        st.switch_page("app.py")
    st.stop()

from recommender import movies_by_genre, all_genres
from ui_helpers  import inject_css, render_topbar, section_header, movie_row
from nav_helper  import render_sidebar

inject_css()
render_topbar()
render_sidebar(current="genre")

movies = st.session_state["movies"]

section_header("🗂️ Browse Movies by Genre")

genres   = all_genres(movies)
selected = st.selectbox("Pick a genre", genres, label_visibility="collapsed")

n_movies = st.slider("How many movies to show", 5, 20, 10)

if selected:
    result = movies_by_genre(selected, movies, top_n=n_movies)
    if result.empty:
        st.info("No movies found for this genre.")
    else:
        section_header(f"🎬 Top {len(result)} — {selected}")
        for start in range(0, len(result), 5):
            chunk = result.iloc[start : start + 5]
            movie_row(
                chunk,
                badge_label=f"🗂️ {selected}",
                badge_class="badge-blue",
                show_scores=False,
                show_fav=True,
                n=5,
            )