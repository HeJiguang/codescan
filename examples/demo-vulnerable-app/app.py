import os
import sqlite3


SECRET_KEY = "demo-secret-key"


def run_backup(user_supplied_target: str) -> int:
    command = f"tar -czf backup.tar.gz {user_supplied_target}"
    return os.system(command)


def find_user(conn: sqlite3.Connection, username: str):
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"
    return conn.execute(query).fetchall()


def render_profile(name: str, bio: str) -> str:
    return f"<h1>{name}</h1><div class='bio'>{bio}</div>"


def debug_headers(headers: dict[str, str]) -> str:
    return headers.get("X-Debug-Token", SECRET_KEY)
