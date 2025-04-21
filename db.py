import sqlite3
import sys


class TrackerDB:
    def __init__(self, db="habits.db"):
        self.db = db
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()
        self._create_table()
        try:
            self.conn = sqlite3.connect(self.db)
            self.cursor = self.conn.cursor()
            self._create_table()
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            print(f"Could not connect to database at {self.db}")

    def _create_table(self):
        """
        Creates habit table and completions tables if they do not exist
        """
        if not self.cursor:
            print("Database cursor not available, cannot create tables.")
            return
        try:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            periodicity TEXT NOT NULL DEFAULT 'daily',
            streak INTEGER NOT NULL DEFAULT 0,
            last_completed TEXT,
            streak_saves INTEGER NOT NULL DEFAULT 0,
            longest_streak INTEGER NOT NULL DEFAULT 0
            );
            """)
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id),
            UNIQUE(habit_id, completion_date)
            );
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database Error during table creation: {e}")
            sys.exit(1)

    def close_connection(self):
        """Closes database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")
