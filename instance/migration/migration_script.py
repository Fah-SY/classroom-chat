import sqlite3
import csv
import os

DB_PATH = r"C:\Users\Ben\PycharmProjects\groupChat2\instance\dev_users.db"
CSV_PATH = "oldProjects.csv"

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
    "users": [
        ("is_admin", "BOOLEAN", 0)
    ]
}

# New Achievement Data
NEW_ACHIEVEMENTS = [
    {"slug": "5d41d731a8d1836b5aa3cba1", "name": "Ch1", "description": "Completion certificate for Ozaria Ch1",
     "type": "certificate", "requirement_value": "1", "reward": 10},
    {"slug": "5d8a57abe8919b28d5113af1", "name": "Ch2", "description": "Completion certificate for Ozaria Ch2",
     "type": "certificate", "requirement_value": "1", "reward": 20},
    {"slug": "5e27600d1c9d440000ac3ee7", "name": "Ch3", "description": "Completion certificate for Ozaria Ch3",
     "type": "certificate", "requirement_value": "1", "reward": 60},
    {"slug": "5f0cb0b7a2492bba0b3520df", "name": "Ch4", "description": "Completion certificate for Ozaria Ch4",
     "type": "certificate", "requirement_value": "1", "reward": 100}
]

# Course ID mapped to new Challenge Value
COURSE_UPDATES = {
    "560f1a9f22961295f9427742": 1,
    "5632661322961295f9428638": 1.5,
    "56462f935afde0c6fd30fc8c": 2,
    "56462f935afde0c6fd30fc8d": 2.5,
    "569ed916efa72b0ced971447": 3,
    "5817d673e85d1220db624ca4": 4,
    "5789587aad86a6efb573701e": 1,
    "57b621e7ad86a6efb5737e64": 2,
    "5a0df02b8f2391437740f74f": 3,
    "65f32b6c87c07dbeb5ba1936": 0.5,
    "5789587aad86a6efb573701f": 1,
    "5789587aad86a6efb5737020": 2,
    "5d41d731a8d1836b5aa3cba1": 1,
    "5d8a57abe8919b28d5113af1": 1.5,
    "5e27600d1c9d440000ac3ee7": 2,
    "5f0cb0b7a2492bba0b3520df": 3
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
        cursor.execute(f"UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Successfully promoted User ID {user_id} to Admin.")
        else:
            print(f"User ID {user_id} not found. No admin promoted.")
    except sqlite3.Error as e:
        print(f"Error promoting user {user_id}: {e}")


def import_csv_data(conn):
    """Imports project data from adjacent CSV file."""
    if not os.path.exists(CSV_PATH):
        print(f"Skipping import: '{CSV_PATH}' not found.")
        return

    print("Importing projects from CSV...")
    cursor = conn.cursor()

    try:
        # Changed to utf-8-sig to handle potential BOM
        # Removed delimiter='\t' (defaults to comma)
        with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)  # Standard CSV reader

            count = 0
            for row in reader:
                name = row.get('name')

                # Skip empty rows
                if not name or not name.strip():
                    continue

                cursor.execute("""
                    INSERT INTO projects (
                        name, description, link, user_id, 
                        teacher_comment, code_snippet, github_link, 
                        video_url, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    row.get('description'),
                    row.get('link'),
                    row.get('user_id'),
                    row.get('teacher_comment'),
                    row.get('code_snippet'),
                    row.get('github_link'),
                    row.get('video_url'),
                    row.get('image_url')
                ))
                count += 1

            conn.commit()
            print(f"Successfully imported {count} projects.")

    except Exception as e:
        print(f"Error importing CSV: {e}")
        if 'row' in locals():
            print(f"Failed on row keys: {row.keys()}")


def run_migrations(conn):
    """Run all defined schema migrations."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cursor.fetchall()}

    # 1. Run Schema Changes
    for table, columns in MIGRATIONS.items():
        if table not in existing_tables:
            print(f"Skipping '{table}' — table not found.")
            continue

        for column_name, column_type, default_value in columns:
            if column_exists(conn, table, column_name):
                # print(f"'{table}.{column_name}' already exists — skipped.")
                continue
            try:
                add_column(conn, table, column_name, column_type, default_value)
            except Exception as e:
                print(f"Error adding '{column_name}' to '{table}':", e)
    print("Schema migration complete.")

    # 2. Run Data Updates
    if "users" in existing_tables:
        promote_user_to_admin(conn, 2)

    # 3. Import CSV Data
    if "projects" in existing_tables:
        import_csv_data(conn)


def seed_achievements(conn):
    """Insert new achievements if they don't exist."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM achievement LIMIT 1")
    except sqlite3.OperationalError:
        print("Table 'achievement' not found. Skipping seed.")
        return

    print("--- Seeding Achievements ---")
    for ach in NEW_ACHIEVEMENTS:
        cursor.execute("SELECT id FROM achievement WHERE slug = ?", (ach['slug'],))
        if cursor.fetchone():
            print(f"Skipping '{ach['name']}' ({ach['slug']}) - already exists.")
            continue

        sql = """
            INSERT INTO achievement (slug, name, description, type, requirement_value, reward)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (ach['slug'], ach['name'], ach['description'], ach['type'], ach['requirement_value'],
                             ach['reward']))
        print(f"Inserted achievement: {ach['name']}")

    conn.commit()
    print("Achievement seeding complete.")


def update_challenge_values(conn):
    """Update challenge_value based on course_id."""
    cursor = conn.cursor()

    # Check if table 'challenge' exists
    try:
        cursor.execute("SELECT 1 FROM challenges LIMIT 1")
    except sqlite3.OperationalError:
        print("Table 'challenges' not found. Skipping challenge updates.")
        return

    print("--- Updating Challenge Values ---")
    count = 0
    for course_id, val in COURSE_UPDATES.items():
        # Update all challenges that belong to this course_id
        cursor.execute("UPDATE challenges SET value = ? WHERE course_id = ?", (val, course_id))
        if cursor.rowcount > 0:
            print(f"Updated course {course_id}: set value to {val} ({cursor.rowcount} rows affected)")
            count += cursor.rowcount

    conn.commit()
    print(f"Challenge value updates complete. Total rows updated: {count}")



if __name__ == "__main__":
    try:
        conn = sqlite3.connect(DB_PATH)
        run_migrations(conn)
        seed_achievements(conn)
        update_challenge_values(conn)  # New function call
    finally:
        if conn:
            conn.close()
            print("Migration complete.")