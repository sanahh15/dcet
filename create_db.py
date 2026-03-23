import sqlite3

# Connect to database (creates database.db if it doesn't exist)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ------------------------
# Users table (admin, instructor, student)
# ------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL  -- admin, instructor, student
)
""")

# ------------------------
# Students table
# ------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ------------------------
# Instructors table
# ------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS instructors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ------------------------
# Study Materials table
# ------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS study_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT,
    instructor_id INTEGER,
    FOREIGN KEY (instructor_id) REFERENCES instructors(id)
)
""")

# ------------------------
# Example table: student-subject mapping
# ------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS student_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject_name TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database recreated successfully!")