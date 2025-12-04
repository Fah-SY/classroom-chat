import sqlite3

DB_PATH = r"C:\Users\Ben\PycharmProjects\groupChat2\instance\dev_users.db"

# Define all desired schema updates here
# Each key = table name, value = list of (column_name, type, default_value)
MIGRATIONS = {
    "achievement": [
        ("icon_class", "VARCHAR(50)", None)
    ],
    "projects": [
        ("teacher_comment", "TEXT", None),
        ("code_snippet", "TEXT", None),
        ("github_link", "VARCHAR(255)", None),
        ("video_url", "VARCHAR(255)", None),
        ("image_url", "VARCHAR(255)", None)
    ],
    "users": [  # CORRECTED: Changed from "user" to "users"
        ("is_admin", "BOOLEAN", 0)
    ]
}


def column_exists(conn, table, column):
    """Check if a column already exists in a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cursor.fetchall())


def add_column(conn, table, column, column_type, default_value):
    """Add a column to a table with a default value."""
    cursor = conn.cursor()
    sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
    if default_value is not None:
        sql += f" DEFAULT {default_value}"
    sql += ";"
    cursor.execute(sql)
    conn.commit()
    print(f"Added '{column}' to '{table}'")


def promote_user_to_admin(conn, user_id):
    """Sets is_admin = 1 for a specific user ID."""
    cursor = conn.cursor()
    try:
        # CORRECTED: Target table 'users' instead of 'user'
        cursor.execute(f"UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))

        if cursor.rowcount > 0:
            conn.commit()
            print(f"Successfully promoted User ID {user_id} to Admin.")
        else:
            print(f"User ID {user_id} not found. No admin promoted.")

    except sqlite3.Error as e:
        print(f"Error promoting user {user_id}: {e}")


def run_migrations():
    """Run all defined migrations on the target database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"Error connecting to database at {DB_PATH}: {e}")
        return

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cursor.fetchall()}

    # 1. Run Schema Changes
    for table, columns in MIGRATIONS.items():
        if table not in existing_tables:
            print(f"Skipping '{table}' — table not found.")
            continue

        for column_name, column_type, default_value in columns:
            if column_exists(conn, table, column_name):
                print(f"'{table}.{column_name}' already exists — skipped.")
                continue
            try:
                add_column(conn, table, column_name, column_type, default_value)
            except Exception as e:
                print(f"Error adding '{column_name}' to '{table}':", e)

    # 2. Run Data Updates (Promote Admin)
    if "users" in existing_tables:
        promote_user_to_admin(conn, 2)

    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    run_migrations()