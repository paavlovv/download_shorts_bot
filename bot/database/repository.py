from datetime import datetime

from .models import get_connection


def add_user(
    user_id: int, username: str = None, first_name: str = None, last_name: str = None
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            last_seen = CURRENT_TIMESTAMP
    """,
        (user_id, username, first_name, last_name),
    )

    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()
    return users


def update_last_seen(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_seen = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """,
        (user_id,),
    )

    conn.commit()
    conn.close()


def get_user_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def add_download_stat(user_id: int, video_url: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO downloads (user_id, video_url)
        VALUES (?, ?)
    """,
        (user_id, video_url),
    )

    conn.commit()
    conn.close()


def get_download_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM downloads")
    count = cursor.fetchone()[0]

    conn.close()
    return count
