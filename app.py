"""
app.py  –  MOAZZIZ Movie Recommender  |  Main entry point
Run with:  streamlit run app.py

Folder structure expected:
    app.py
    database.py
    recommender.py
    ui_helpers.py
    nav_helper.py          ← NEW: shared sidebar helper
    .streamlit/
        pages.toml         ← NEW: explicit page registration
    pages/
        1_Recommendations.py
        2_Browse_by_Genre.py
        3_My_Favourites.py
        4_Watch_History.py
"""

import streamlit as st

st.set_page_config(
    page_title="MOAZZIZ | Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",   # CSS below prevents it ever collapsing
)

from database    import init_db, login_user, register_user, get_favourites
from recommender import load_data, compute_similarity, fetch_poster
from ui_helpers  import inject_css, render_topbar, section_header, movie_row
from nav_helper  import render_sidebar

#init_db()
inject_css()

# ── Force sidebar to always stay open (hide the collapse arrow) ─────────────
st.markdown(
    """
    <style>
        /* Hide the collapse/expand arrow button */
        button[kind="header"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }

        /* Always keep sidebar visible and at fixed width */
        section[data-testid="stSidebar"] {
            min-width: 240px !important;
            max-width: 240px !important;
            transform: none !important;
            visibility: visible !important;
        }

        /* Remove any translate that Streamlit applies when collapsing */
        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: none !important;
            margin-left: 0 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

MOVIES_CSV  = r"G:\My Drive\movies data set\tmdb_5000_movies.csv"
CREDITS_CSV = r"G:\My Drive\credit data set\tmdb_5000_credits.csv"

movies     = load_data(MOVIES_CSV, CREDITS_CSV)
cosine_sim = compute_similarity(movies["tags"])

if "movies" not in st.session_state:
    st.session_state["movies"]     = movies
if "cosine_sim" not in st.session_state:
    st.session_state["cosine_sim"] = cosine_sim


# ════════════════════════════════════════════════════════════════════════════
#  AUTH GATE
# ════════════════════════════════════════════════════════════════════════════
def auth_page():
    st.markdown(
        """
        <div style="text-align:center; padding: 30px 0 10px;">
            <span style="font-size:52px; font-weight:900;
                         background:linear-gradient(135deg,#bb86fc,#8b5cf6);
                         -webkit-background-clip:text;
                         -webkit-text-fill-color:transparent;">
                🎬 MOAZZIZ
            </span><br>
            <span style="color:#888; font-size:15px;">
                Your personal AI-powered movie companion
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        tab_login, tab_register = st.tabs(["🔐  Log In", "📝  Register"])

        with tab_login:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", key="li_username",
                                     placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="li_password",
                                     placeholder="Enter your password")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if st.button("Log In", use_container_width=True, key="btn_login"):
                if not username or not password:
                    st.warning("Please fill in both fields.")
                else:
                    user = login_user(username.strip(), password)
                    if user:
                        st.session_state["user"]       = user
                        st.session_state["favourites"] = get_favourites(user["id"])
                        st.success(f"Welcome back, **{user['username']}**! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password.")

        with tab_register:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            new_user  = st.text_input("Username",         key="reg_username",
                                      placeholder="Choose a username")
            new_email = st.text_input("Email",            key="reg_email",
                                      placeholder="your@email.com")
            new_pass  = st.text_input("Password",         type="password",
                                      key="reg_pass",  placeholder="Min 6 characters")
            new_pass2 = st.text_input("Confirm Password", type="password",
                                      key="reg_pass2", placeholder="Repeat password")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if st.button("Create Account", use_container_width=True, key="btn_register"):
                if not all([new_user, new_email, new_pass, new_pass2]):
                    st.warning("Please fill in all fields.")
                elif len(new_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(new_user.strip(), new_email.strip(), new_pass)
                    if ok:
                        st.success(msg + " Switch to the Log In tab.")
                    else:
                        st.error(f"❌ {msg}")


# ════════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ════════════════════════════════════════════════════════════════════════════
def home_page():
    render_topbar()
    render_sidebar(current="home")

    st.markdown("### 🔍 Find a Movie")
    movie_list = movies["title"].tolist()
    search_col, btn_col = st.columns([5, 1])
    with search_col:
        selected = st.selectbox(
            "Search movie", movie_list,
            label_visibility="collapsed",
            key="home_search",
        )
    with btn_col:
        st.write("")
        if st.button("🎬 Recommend", use_container_width=True, key="home_go"):
            st.session_state["selected_movie"] = selected
            st.switch_page("pages/1_Recommendations.py")

    st.markdown("---")

    section_header("⭐ Moazziz Favourites")
    owner_fav_titles = [
        "No Country for Old Men", "The Intern",
        "Mission: Impossible - Ghost Protocol",
        "Interstellar", "The Dark Knight",
    ]
    owner_df = movies[movies["title"].isin(owner_fav_titles)].copy()
    movie_row(owner_df, badge_label="⭐ Owner Fav", badge_class="badge-gold", show_fav=True)

    section_header("🔥 Trending Now")
    popular_df = movies.sort_values("popularity", ascending=False).head(5)
    movie_row(popular_df, badge_label="🔥 Trending", badge_class="badge-red", show_fav=True)

    section_header("⭐ Top IMDb Rated")
    imdb_df = movies.sort_values("vote_average", ascending=False).head(5)
    movie_row(imdb_df, badge_label=None, badge_class="badge-green", show_fav=True)

    section_header("🎬 Top Picks for You")
    movies["_netflix_score"] = (
        movies["popularity"] * 0.5
        + movies["vote_average"] * 10 * 0.3
        + movies["vote_count"] * 0.0001 * 0.2
    )
    netflix_df = movies.sort_values("_netflix_score", ascending=False).head(5)
    movie_row(netflix_df, badge_label="🎬 Top Pick", badge_class="badge-blue", show_fav=True)


# ════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.get("user"):
    home_page()
else:
    auth_page()
