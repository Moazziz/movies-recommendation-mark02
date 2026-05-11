"""
pages/1_Recommendations.py
Full recommendation results page with hybrid scoring display.
"""

import streamlit as st

st.set_page_config(page_title="Recommendations | MOAZZIZ", page_icon="🔍", layout="wide")

if "user" not in st.session_state:
    st.warning("🔒 Please log in first.")
    if st.button("← Go to Login", key="login_redirect"):
        st.switch_page("app.py")
    st.stop()

from recommender import recommend_movies, fetch_poster
from database    import add_to_history
from ui_helpers  import inject_css, render_topbar, section_header, movie_row, movie_card
from nav_helper  import render_sidebar

inject_css()
render_topbar()
render_sidebar(current="reco")

movies     = st.session_state["movies"]
cosine_sim = st.session_state["cosine_sim"]

section_header("🔍 Get Movie Recommendations")

movie_list  = movies["title"].tolist()
default_idx = (
    movie_list.index(st.session_state["selected_movie"])
    if st.session_state.get("selected_movie") in movie_list
    else 0
)

col_sel, col_btn = st.columns([5, 1])
with col_sel:
    selected = st.selectbox(
        "Choose a movie", movie_list,
        index=default_idx,
        label_visibility="collapsed",
    )
with col_btn:
    st.write("")
    go = st.button("🎬 Recommend", use_container_width=True)

exp = st.expander("⚙️ Filter options", expanded=False)
with exp:
    c1, c2 = st.columns(2)
    top_n      = c1.slider("Number of recommendations", 5, 20, 10)
    min_rating = c2.slider("Minimum IMDb rating",       5.0, 9.0, 6.5, 0.5)

if go or st.session_state.get("selected_movie"):
    st.session_state["selected_movie"] = selected
    add_to_history(st.session_state["user"]["id"], selected)

    with st.spinner("🎬 Finding the best matches…"):
        result = recommend_movies(
            selected, movies, cosine_sim,
            top_n=top_n, min_rating=min_rating,
        )

    if result is None or result.empty:
        st.error("😕 No recommendations found. Try a different movie or lower the rating filter.")
    else:
        st.markdown("---")
        section_header(f"Because you like:  {selected}")
        sel_row = movies[movies["title"] == selected].iloc[0]
        c_img, c_info = st.columns([1, 3])
        with c_img:
            st.image(fetch_poster(selected), width=200)
        with c_info:
            genres = ", ".join(sel_row["genres"]) if sel_row["genres"] else "—"
            st.markdown(f"**Genres:** {genres}")
            st.markdown(f"**IMDb:** ⭐ {round(sel_row['vote_average'], 1)}")
            st.markdown(f"**Popularity rank:** 🔥 {round(sel_row['popularity'], 1)}")
            overview = sel_row["overview"]
            st.markdown(
                f"**Overview:** {overview[:300]}…"
                if len(overview) > 300 else overview
            )

        st.markdown("---")
        section_header("🎯 Top Recommendations")
        n_cols = min(5, len(result))
        cols   = st.columns(n_cols)
        for idx, (_, row) in enumerate(result.iterrows()):
            movie_card(
                col          = cols[idx % n_cols],
                title        = row["title"],
                vote_average = row["vote_average"],
                badge_label  = f"#{idx+1} Match",
                badge_class  = "badge-purple",
                similarity   = row["similarity"],
                final_score  = row["final_score"],
                show_fav_btn = True,
            )

        st.markdown("---")
        section_header("📊 Score Breakdown")
        st.markdown(
            """
            | Weight | Factor | Description |
            |--------|--------|-------------|
            | **50%** | 🎯 Similarity | Content-based cosine similarity on genres, keywords, cast & crew |
            | **30%** | ⭐ IMDb | Normalised audience rating (filtered ≥ min rating) |
            | **20%** | 🔥 Popularity | Weighted blend of TMDB popularity + log-vote-count |
            """
        )