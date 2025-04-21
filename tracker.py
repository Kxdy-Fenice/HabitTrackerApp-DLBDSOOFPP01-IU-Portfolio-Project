import sqlite3
from habit import Habit
from db import TrackerDB
from datetime import date


class Tracker:
    def __init__(self, db="habits.db"):
        self.db = TrackerDB(db)
        self.cursor = self.db.conn.cursor()

    def _habit_from_row(self, row):
        """
        Function to create a Habit object from a database row
        """

        last_completed_val = row[4]
        habit_last_completed = None

        if last_completed_val:
            try:
                habit_last_completed = date.fromisoformat(last_completed_val)
            except (ValueError, TypeError):
                print(f"Warning: Invalid date format '{last_completed_val}' found in database for habit '{row[1]}'. "
                      f"Setting last_completed to None.")
                habit_last_completed = None

        return Habit(
            name=row[1],
            periodicity=row[2],
            streak=row[3],
            last_completed=habit_last_completed,
            streak_saves=row[5],
            longest_streak=row[6]
        )

    def _get_habit_id(self, habit_name):
        """
        Fetch the habit's unique ID
        :param habit_name: name of the habit
        """
        self.cursor.execute("SELECT id FROM habits WHERE name=?", (habit_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def list_all_habit_names(self):
        """
        Fetches a list of all habit names
        """
        try:
            self.cursor.execute("SELECT name FROM habits ORDER BY name")
            rows = self.cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            print(f"Database error while listing habits: {e}")
            return []

    def list_habits_by_periodicity(self, periodicity):
        """
        Fetches a list of all habits  with the specified periodicity
        :param periodicity: The periodicity, i.e., daily, weekly, monthly
        :return: A list of habits with the specified periodicity
        """
        if periodicity not in ['daily', 'weekly', 'monthly']:
            print(f"Warning: Invalid periodicity '{periodicity}' provided. Returning empty list.")
            return []

        try:
            self.cursor.execute("SELECT * FROM habits WHERE periodicity=?", (periodicity,))
            rows = self.cursor.fetchall()

            habits_list = [self._habit_from_row(row) for row in rows]

            return habits_list

        except sqlite3.Error as e:
            print(f"Database error while listing habits by periodicity '{periodicity}': {e}")
            return []

    def create_habit(self, name, periodicity='daily'):
        """
        Creates new habit and adds it to the database
        :param name: name of the habit
        :param periodicity: periodicity of the habit, i.e., daily, weekly or monthly
        """
        try:
            self.cursor.execute(
                "INSERT INTO habits (name, periodicity, longest_streak) VALUES (?, ?, ?)",
                (name, periodicity, 0)
            )
            self.db.conn.commit()
            print(f"'{periodicity}' habit created: '{name}'")
            return self.get_habit(name)
        except sqlite3.IntegrityError:
            print(f"Habit with name '{name}' already exists.")
            return self.get_habit(name)

    def get_habit(self, name):
        """
        Fetches habit by name from the database
        :param name: name of the habit
        """
        self.cursor.execute("SELECT * FROM habits WHERE name=?", (name,))
        row = self.cursor.fetchone()
        if row:
            return self._habit_from_row(row)
        return None

    def edit_habit(self, name, new_name=None, new_periodicity=None, new_longest_streak=None):
        """
        Edit an existing habit's name or periodicity
        :param name: name of the habit
        :param new_name: new name of the habit
        :param new_periodicity: new periodicity of the habit
        :param new_longest_streak: new longest streak of the habit
        """
        habit = self.get_habit(name)
        if not habit:
            print(f"Habit '{name}' not found")
            return

        if new_name:
            try:
                self.cursor.execute("UPDATE habits SET name=? WHERE name=?", (new_name, name))
                habit.name = new_name
                print(f"Habit name update to '{new_name}'.")
            except sqlite3.IntegrityError:
                print(f"Habit with name '{new_name}' already exists.")
                return

        if new_periodicity and new_periodicity in ['daily', 'weekly', 'monthly']:
            self.cursor.execute("UPDATE habits SET periodicity=? WHERE name=?", (new_periodicity, habit.name))
            habit.periodicity = new_periodicity
            print(f"Periodicity for '{habit.name}' updated to '{new_periodicity}'.")
        elif new_periodicity:
            print("Invalid periodicity. Please choose 'daily', 'weekly', or 'monthly'.")

        if new_longest_streak is not None and isinstance(new_longest_streak, int) and new_longest_streak >= 0:
            self.cursor.execute("UPDATE habits SET longest_streak=? WHERE name=?", (new_longest_streak, habit.name))
            habit.longest_streak = new_longest_streak
            print(f"Longest streak for '{habit.name}' updated to {new_longest_streak}.")
        elif new_longest_streak is not None:
            print("Invalid longest streak value.")

        self._save_habit(habit)
        self.db.conn.commit()
        return habit

    def update_habit(self, habit):
        """
        Updates the habit's streak, last_completed, streak_saves, and the longest_streak in the database
        :param habit: name of the habit
        """
        last_completed_str = habit.last_completed.isoformat() if habit.last_completed else None

        self.cursor.execute(
            """
            UPDATE habits SET streak=?, last_completed=?, streak_saves=?, longest_streak=? WHERE name=?
            """,
            (habit.streak, habit.last_completed, habit.streak_saves, habit.longest_streak, habit.name)
        )
        self.db.conn.commit()
        print(f"Habit '{habit.name}' updated in the database.")

    def _save_habit(self, habit):
        """
        Save the current state of a Habit object to the database.
        :param habit: name of the habit
        """
        self.update_habit(habit)

    def delete_habit(self, name):
        """
        Delete a specified habit from the database.
        :param name: name of the habit
        """
        self.cursor.execute("DELETE FROM habits WHERE name=?", (name,))
        if self.cursor.rowcount > 0:
            self.db.conn.commit()
            print(f"Habit '{name}' deleted.")
        else:
            print(f"Habit '{name}' not found.")

    def record_completion(self, name):
        """
        Records a habit completion, updating its streak and logging the date.
        :param name: name of the habit
        """
        habit = self.get_habit(name)
        if habit:
            habit.increment()
            self.update_habit(habit)
            habit_id = self._get_habit_id(name)
            if habit_id:
                today_str = date.today().strftime('%Y-%m-%d')
                try:
                    self.cursor.execute(
                        "INSERT INTO completions (habit_id, completion_date) VALUES (?, ?)",
                        (habit_id, today_str)
                    )
                    self.db.conn.commit()
                    print(f"Completion recorded for '{name}' on {date.today()}.")
                except sqlite3.IntegrityError:
                    print(f"Completion for '{name}' on {date.today()} already logged.")
        else:
            print(f"Habit '{name}' not found.")

    def get_completion_history(self, habit_name):
        """
        Fetches completion history of a specified habit
        :param habit_name: name of the habit
        """
        habit_id = self._get_habit_id(habit_name)
        if habit_id:
            self.cursor.execute(
                "SELECT completion_date FROM completions WHERE habit_id=?",
                (habit_id,)
            )
            rows = self.cursor.fetchall()
            return [date.fromisoformat(row[0]) for row in rows]
        return []

    def close_connection(self):
        """Closes the database connection."""
        self.db.close_connection()
