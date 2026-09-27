import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "users.db"


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# PASSWORD HASH
# ============================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# DATABASE INIT
# ============================================================

def init_db():

    connection = get_connection()
    cursor = connection.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # SESSIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # COMMUNICATION HISTORY
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # FAVORITES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, message),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # EMERGENCY CONTACTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, phone),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(name: str, email: str, password: str):

    connection = get_connection()

    try:

        password_hash = hash_password(password)

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users
            (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email.lower().strip(),
            password_hash,
            datetime.now(timezone.utc).isoformat()
        ))

        connection.commit()

        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "name": name,
            "email": email.lower().strip()
        }

    except sqlite3.IntegrityError:

        return None

    finally:

        connection.close()


def get_user_by_email(email: str):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        email.lower().strip(),
    ))

    user = cursor.fetchone()

    connection.close()

    return user


def verify_user(email: str, password: str):

    user = get_user_by_email(email)

    if not user:
        return None

    if user["password_hash"] != hash_password(password):
        return None

    return user


# ============================================================
# SESSION FUNCTIONS
# ============================================================

def create_session(user_id: int):

    token = secrets.token_urlsafe(32)

    connection = get_connection()

    connection.execute("""
        INSERT INTO sessions
        (user_id, token, created_at)
        VALUES (?, ?, ?)
    """, (
        user_id,
        token,
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()

    return token


def get_user_by_session(token: str):

    if not token:
        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT users.*
        FROM sessions
        JOIN users
        ON users.id = sessions.user_id
        WHERE sessions.token = ?
    """, (
        token,
    ))

    user = cursor.fetchone()

    connection.close()

    return user


def delete_session(token: str):

    connection = get_connection()

    connection.execute("""
        DELETE FROM sessions
        WHERE token = ?
    """, (
        token,
    ))

    connection.commit()
    connection.close()


# ============================================================
# HISTORY
# ============================================================

def add_history(
    user_id: int,
    source: str,
    message: str
):

    connection = get_connection()

    connection.execute("""
        INSERT INTO communication_history
        (user_id, source, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        source,
        message,
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()


def get_history(user_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            source,
            message,
            created_at
        FROM communication_history
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


def clear_history(user_id: int):

    connection = get_connection()

    connection.execute("""
        DELETE FROM communication_history
        WHERE user_id = ?
    """, (
        user_id,
    ))

    connection.commit()
    connection.close()


# ============================================================
# FAVORITES
# ============================================================

def add_favorite(
    user_id: int,
    message: str
):

    connection = get_connection()

    connection.execute("""
        INSERT OR IGNORE INTO favorites
        (user_id, message, created_at)
        VALUES (?, ?, ?)
    """, (
        user_id,
        message,
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()


def get_favorites(user_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            message,
            created_at
        FROM favorites
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


def delete_favorite(
    user_id: int,
    message: str
):

    connection = get_connection()

    connection.execute("""
        DELETE FROM favorites
        WHERE user_id = ?
        AND message = ?
    """, (
        user_id,
        message
    ))

    connection.commit()
    connection.close()


# ============================================================
# EMERGENCY CONTACTS
# ============================================================

def add_emergency_contact(
    user_id: int,
    name: str,
    phone: str
):

    connection = get_connection()

    connection.execute("""
        INSERT OR IGNORE INTO emergency_contacts
        (user_id, name, phone, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        name,
        phone,
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()


def get_emergency_contacts(user_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            phone,
            created_at
        FROM emergency_contacts
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


def delete_emergency_contact(
    user_id: int,
    phone: str
):

    connection = get_connection()

    connection.execute("""
        DELETE FROM emergency_contacts
        WHERE user_id = ?
        AND phone = ?
    """, (
        user_id,
        phone
    ))

    connection.commit()
    connection.close()


# ============================================================
# START DATABASE
# ============================================================

init_db()