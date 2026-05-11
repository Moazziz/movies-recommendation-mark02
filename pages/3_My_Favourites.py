"""
pages/3_My_Favourites.py
User's saved favourite movies with remove option.
"""

import streamlit as st

st.set_page_config(page_title="My Favourites | MOAZZIZ", page_icon="❤️", layout="wide")

if "user" not in st.session_state:
    st.warning("🔒 Please log in first.")
    if st.button("← Go to Login", key="login_redirect"):
        st.switch_page("app.py")
    st.stop()

from database   import get_favourites, remove_favourite
from ui_helpers import inject_css, render_topbar, section_header, movie_row
from nav_helper import render_sidebar

inject_css()
render_topbar()
render_sidebar(current="fav")

movies  = st.session_state["movies"]
user_id = st.session_state["user"]["id"]

st.session_state["favourites"] = get_favourites(user_id)
favs = st.session_state["favourites"]

section_header("❤️ My Favourite Movies")

if not favs:
    st.info("You haven't saved any favourites yet. Click the 🤍 Save button on any movie!")
else:
    st.markdown(f"**{len(favs)} saved movie(s)**")
    fav_df = movies[movies["title"].isin(favs)].copy()
    for start in range(0, len(fav_df), 5):
        chunk = fav_df.iloc[start : start + 5]
        movie_row(
            chunk,
            badge_label="❤️ Favourite",
            badge_class="badge-gold",
            show_fav=True,
            n=5,
        )