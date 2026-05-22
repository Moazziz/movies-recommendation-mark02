"""
database.py  –  MySQL connection + user-management helpers
All passwords are stored as bcrypt hashes (never plain text).
"""

import mysql.connector
from mysql.connector import Error
import bcrypt
import streamlit as st


# ──────────────────────────────────────────────
# CONFIG  (edit to match your MySQL server)
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",          # ← your MySQL username
    "password": "19MMB128gj9109", # ← your MySQL password
    "database": "moviesDB",
}


# ──────────────────────────────────────────────
# CONNECTION
# ──────────────────────────────────────────────
#abhi comment kiya hai 23/4/26
def get_connection():
    """Return a live MySQL connection, or None on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

# ──────────────────────────────────────────────
# SCHEMA BOOTSTRAP  (run once at startup)
# ──────────────────────────────────────────────
# def init_db():
#     """Create the database + tables if they don't exist yet."""
#     try:
#         # Connect WITHOUT specifying the database first
#         cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
#         conn = mysql.connector.connect(**cfg)
#         cur  = conn.cursor()

#         cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
#         cur.execute(f"USE {DB_CONFIG['database']}")

#         # ── users table ──────────────────────────────────────────
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 id            INT AUTO_INCREMENT PRIMARY KEY,
#                 username      VARCHAR(80)  UNIQUE NOT NULL,
#                 email         VARCHAR(150) UNIQUE NOT NULL,
#                 password_hash VARCHAR(255) NOT NULL,
#                 created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
#             )
#         """)

#         # ── watch history table ──────────────────────────────────
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS watch_history (
#                 id          INT AUTO_INCREMENT PRIMARY KEY,
#                 user_id     INT NOT NULL,
#                 movie_title VARCHAR(255) NOT NULL,
#                 watched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
#             )
#         """)

#         # ── user favourites table ────────────────────────────────
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS user_favourites (
#                 id          INT AUTO_INCREMENT PRIMARY KEY,
#                 user_id     INT NOT NULL,
#                 movie_title VARCHAR(255) NOT NULL,
#                 added_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE KEY uq_fav (user_id, movie_title),
#                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
#             )
#         """)

#         conn.commit()
#         cur.close()
#         conn.close()
#         return True

#     except Error as e:
#         st.error(f"❌ DB init error: {e}")
#         return False
# ──────────────────────────────────────────────
# SCHEMA BOOTSTRAP  (run once at startup)
# ──────────────────────────────────────────────
def init_db():
    """Create the database + tables if they don't exist yet."""
    try:
        # Connect WITHOUT specifying the database first
        cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        conn = mysql.connector.connect(**cfg)
        cur  = conn.cursor()

        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cur.execute(f"USE {DB_CONFIG['database']}")

        # ── users table ──────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                username      VARCHAR(80) UNIQUE NOT NULL,
                email         VARCHAR(150) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── watch history table ──────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watch_history (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                movie_title VARCHAR(255) NOT NULL,
                watched_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # ── user favourites table ────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_favourites (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                movie_title VARCHAR(255) NOT NULL,
                added_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_fav (user_id, movie_title),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Error as e:
        st.error(f"❌ DB init error: {e}")
        return False

# ──────────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def register_user(username: str, email: str, password: str):
    """
    Insert a new user.
    Returns (True, "success message") or (False, "error message").
    """
    conn = get_connection()
    if not conn:
        return False, "Could not connect to database."
    try:
        cur = conn.cursor()
        pw_hash = hash_password(password)
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, pw_hash),
        )
        conn.commit()
        return True, "Registration successful! Please log in."
    except mysql.connector.IntegrityError:
        return False, "Username or email already exists."
    except Error as e:
        return False, str(e)
    finally:
        cur.close()
        conn.close()


def login_user(username: str, password: str):
    """
    Validate credentials.
    Returns the user row dict on success, None on failure.
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,),
        )
        user = cur.fetchone()
        if user and verify_password(password, user["password_hash"]):
            return user
        return None
    except Error:
        return None
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# WATCH HISTORY
# ──────────────────────────────────────────────
def add_to_history(user_id: int, movie_title: str):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO watch_history (user_id, movie_title) VALUES (%s, %s)",
            (user_id, movie_title),
        )
        conn.commit()
    except Error:
        pass
    finally:
        cur.close()
        conn.close()


def get_history(user_id: int):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT movie_title, watched_at
               FROM watch_history
               WHERE user_id = %s
               ORDER BY watched_at DESC
               LIMIT 20""",
            (user_id,),
        )
        return cur.fetchall()
    except Error:
        return []
    finally:
        cur.close()
        conn.close()


# ──────────────────────────────────────────────
# FAVOURITES
# ──────────────────────────────────────────────
def add_favourite(user_id: int, movie_title: str):
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO user_favourites (user_id, movie_title) VALUES (%s, %s)",
            (user_id, movie_title),
        )
        conn.commit()
        return cur.rowcount > 0
    except Error:
        return False
    finally:
        cur.close()
        conn.close()


def remove_favourite(user_id: int, movie_title: str):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM user_favourites WHERE user_id=%s AND movie_title=%s",
            (user_id, movie_title),
        )
        conn.commit()
    except Error:
        pass
    finally:
        cur.close()
        conn.close()


def get_favourites(user_id: int):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT movie_title FROM user_favourites WHERE user_id=%s ORDER BY added_at DESC",
            (user_id,),
        )
        return [r["movie_title"] for r in cur.fetchall()]
    except Error:
        return []
    finally:
        cur.close()
        conn.close()
