import unittest
import sqlite3
from datetime import date, timedelta
from unittest.mock import patch
from tracker import Tracker
from habit import Habit
from db import TrackerDB

TODAY = date(2025, 4, 15)
YESTERDAY = TODAY - timedelta(days=1)
LAST_WEEK = TODAY - timedelta(weeks=1)


class TestTracker(unittest.TestCase):

    def setUp(self):
        """
        In-memory database and tracker for each test
        """
        self.db_instance = TrackerDB(db=":memory:")
        self.tracker = Tracker(db=":memory:")
        self.tracker.db = self.db_instance
        self.tracker.cursor = self.db_instance.cursor

    def tearDown(self):
        """
        Closes database connection after each test
        """
        self.tracker.close_connection()

    # -- Test Habit Creation --

    def test_create_habit_daily(self):
        """
        Test successful creation of a habit
        """
        habit_name = "Drink Water"
        habit = self.tracker.create_habit(habit_name, 'daily')
        self.assertIsNotNone(habit)
        self.assertEqual(habit.name, habit_name)
        self.assertEqual(habit.periodicity, 'daily')
        self.assertEqual(habit.streak, 0)
        self.assertIsNone(habit.last_completed)
        self.assertEqual(habit.longest_streak, 0)

        self.tracker.cursor.execute("SELECT name, periodicity, streak FROM habits WHERE name=?", (habit_name,))
        row = self.tracker.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], habit_name)
        self.assertEqual(row[1], 'daily')
        self.assertEqual(row[2], 0)

    def test_create_habit_weekly(self):
        """
        Test successful creation of a weekly habit
        """
        habit_name = "Review Goals"
        habit = self.tracker.create_habit(habit_name, 'weekly')
        self.assertIsNotNone(habit)
        self.assertEqual(habit.name, habit_name)
        self.assertEqual(habit.periodicity, 'weekly')

        retrieved_habit = self.tracker.get_habit(habit_name)
        self.assertEqual(retrieved_habit.periodicity, 'weekly')

    def test_create_habit_duplicate(self):
        """
        Test creation of a habit with a name of a habit that already exists
        """
        habit_name = "Exercise"
        self.tracker.create_habit(habit_name, 'daily')
        habit_duplicate = self.tracker.create_habit(habit_name, 'daily')
        self.assertIsNotNone(habit_duplicate)
        self.assertEqual(habit_duplicate.name, habit_name)

        self.tracker.cursor.execute("SELECT COUNT(*) FROM habits WHERE name=?", (habit_name,))
        count = self.tracker.cursor.fetchone()[0]
        self.assertEqual(count, 1)

    # -- Test Habit Retrieval --
    def test_get_habit_exists(self):
        """
        Test retrieving an existing habit
        """
        habit_name = "Meditate"
        self.tracker.create_habit(habit_name, 'daily')
        habit = self.tracker.get_habit(habit_name)
        self.assertIsNotNone(habit)
        self.assertEqual(habit.name, habit_name)
        self.assertIsInstance(habit, Habit)

    def test_get_habit_not_exists(self):
        """
        Test retrieving a non-existent habit
        """
        habit = self.tracker.get_habit("NonExistentHabit")
        self.assertIsNone(habit)

    # --- Test Habit Deletion ---

    def test_delete_habit_exists(self):
        """
        Test deleting an existing habit
        """
        habit_name = "Read"
        self.tracker.create_habit(habit_name, 'daily')
        self.assertIsNotNone(self.tracker.get_habit(habit_name))
        self.tracker.delete_habit(habit_name)
        self.assertIsNone(self.tracker.get_habit(habit_name))

        self.tracker.cursor.execute("SELECT COUNT(*) FROM habits WHERE name=?", (habit_name,))
        count = self.tracker.cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_delete_habit_not_exists(self):
        """
        Test deleting a non-existent habit
        """
        try:
            self.tracker.delete_habit("GhostHabit")
        except Exception as e:
            self.fail(f"Deleting non-existent habit raised an exception: {e}")

    # --- Test Completion Recording & Streaks ---

    @patch('habit.date')
    @patch('tracker.date')
    def test_record_completion_daily_first_time(self, mock_tracker_date, mock_habit_date):
        """
        Test recording the first completion for a daily habit
        """
        mock_tracker_date.today.return_value = TODAY
        mock_habit_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat

        habit_name = "Stretch"
        self.tracker.create_habit(habit_name, 'daily')
        self.tracker.record_completion(habit_name)

        habit = self.tracker.get_habit(habit_name)
        self.assertEqual(habit.streak, 1)
        self.assertEqual(habit.last_completed, TODAY)
        self.assertEqual(habit.longest_streak, 1)

        history = self.tracker.get_completion_history(habit_name)
        self.assertEqual(len(history), 1)
        self.assertIn(TODAY, history)

    @patch('habit.date')
    @patch('tracker.date')
    def test_record_completion_daily_consecutive(self, mock_tracker_date, mock_habit_date):
        """
        Test recording a consecutive completion for a daily habit
        """
        habit_name = "Journal"
        self.tracker.create_habit(habit_name, 'daily')
        habit_id = self.tracker._get_habit_id(habit_name)
        self.tracker.cursor.execute(
            "UPDATE habits SET streak=1, last_completed=?, longest_streak=1 WHERE id=?",
            (YESTERDAY.isoformat(), habit_id)
        )
        self.tracker.cursor.execute(
            "INSERT INTO completions (habit_id, completion_date) VALUES (?, ?)",
            (habit_id, YESTERDAY.isoformat())
        )
        self.tracker.db.conn.commit()

        mock_tracker_date.today.return_value = TODAY
        mock_habit_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat
        mock_habit_date.fromisoformat.side_effect = date.fromisoformat

        self.tracker.record_completion(habit_name)

        habit = self.tracker.get_habit(habit_name)
        self.assertEqual(habit.streak, 2)
        self.assertEqual(habit.last_completed, TODAY)
        self.assertEqual(habit.longest_streak, 2)

        history = self.tracker.get_completion_history(habit_name)
        self.assertEqual(len(history), 2)
        self.assertIn(TODAY, history)
        self.assertIn(YESTERDAY, history)

    @patch('habit.date')
    @patch('tracker.date')
    def test_record_completion_daily_same_day(self, mock_tracker_date, mock_habit_date):
        """
        Test recording completion twice on the same day for a daily habit
        """
        mock_tracker_date.today.return_value = TODAY
        mock_habit_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat

        habit_name = "Pushups"
        self.tracker.create_habit(habit_name, 'daily')
        self.tracker.record_completion(habit_name)
        habit_after_first = self.tracker.get_habit(habit_name)
        self.assertEqual(habit_after_first.streak, 1)

        self.tracker.record_completion(habit_name)

        habit_after_second = self.tracker.get_habit(habit_name)
        self.assertEqual(habit_after_second.streak, 1)
        self.assertEqual(habit_after_second.last_completed, TODAY)
        self.assertEqual(habit_after_second.longest_streak, 1)

        history = self.tracker.get_completion_history(habit_name)
        self.assertEqual(len(history), 1)
        self.assertIn(TODAY, history)

    @patch('habit.date')
    @patch('tracker.date')
    def test_record_completion_daily_break_streak(self, mock_tracker_date, mock_habit_date):
        """
        Test that the streak resets if a day is missed.
        Simulating streak of 5 with last completion of two days ago.
        """
        habit_name = "Walk"
        self.tracker.create_habit(habit_name, 'daily')
        habit_id = self.tracker._get_habit_id(habit_name)

        day_before_yesterday = TODAY - timedelta(days=2)
        self.tracker.cursor.execute(
            "UPDATE habits SET streak=5, last_completed=?, longest_streak=5 WHERE id=?",
            (day_before_yesterday.isoformat(), habit_id)
        )
        self.tracker.db.conn.commit()

        mock_tracker_date.today.return_value = TODAY
        mock_habit_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat
        mock_habit_date.fromisoformat.side_effect = date.fromisoformat

        habit_before = self.tracker.get_habit(habit_name)
        habit_before.streak_reset()
        self.tracker.update_habit(habit_before)
        self.tracker.record_completion(habit_name)

        habit_after = self.tracker.get_habit(habit_name)
        self.assertEqual(habit_after.streak, 1, "Streak should reset to 0 and then increment to 1")
        self.assertEqual(habit_after.last_completed, TODAY)
        self.assertEqual(habit_after.longest_streak, 5)

    @patch('habit.date')
    @patch('tracker.date')
    def test_record_completion_weekly_within_period(self, mock_tracker_date, mock_habit_date):
        """
        Test weekly habit completion within the same week
        """
        habit_name = "Plan Week"
        self.tracker.create_habit(habit_name, 'weekly')
        habit_id = self.tracker._get_habit_id(habit_name)

        two_days_ago = TODAY - timedelta(days=2)
        self.tracker.cursor.execute(
            "UPDATE habits SET streak=1, last_completed=?, longest_streak=1 WHERE id=?",
            (two_days_ago.isoformat(), habit_id)
        )
        self.tracker.db.conn.commit()

        mock_tracker_date.today.return_value = TODAY
        mock_habit_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat
        mock_habit_date.fromisoformat.side_effect = date.fromisoformat

        self.tracker.record_completion(habit_name)

        habit = self.tracker.get_habit(habit_name)
        self.assertEqual(habit.streak, 1)
        self.assertEqual(habit.last_completed, two_days_ago)

    # --- Test Habit Editing ---

    def test_edit_habit_name_success(self):
        """
        Test successfully editing a habit's name
        """
        old_name = "Workout"
        new_name = "Gym Session"
        self.tracker.create_habit(old_name, 'daily')
        updated_habit = self.tracker.edit_habit(old_name, new_name=new_name)

        self.assertIsNotNone(updated_habit)
        self.assertEqual(updated_habit.name, new_name)
        self.assertIsNone(self.tracker.get_habit(old_name))
        self.assertIsNotNone(self.tracker.get_habit(new_name))

    def test_edit_habit_name_to_existing(self):
        """
        Test editing a habit name to one that already exists
        """
        name1 = "Habit A"
        name2 = "Habit B"
        self.tracker.create_habit(name1, 'daily')
        self.tracker.create_habit(name2, 'weekly')

        updated_habit = self.tracker.edit_habit(name1, new_name=name2)
        self.assertIsNone(updated_habit)

        self.assertIsNotNone(self.tracker.get_habit(name1))
        self.assertEqual(self.tracker.get_habit(name1).name, name1)
        self.assertIsNotNone(self.tracker.get_habit(name2))

    def test_edit_habit_periodicity_success(self):
        """
        Test successfully editing a habit's periodicity
        """
        habit_name = "Clean Desk"
        self.tracker.create_habit(habit_name, 'daily')
        updated_habit = self.tracker.edit_habit(habit_name, new_periodicity='weekly')

        self.assertIsNotNone(updated_habit)
        self.assertEqual(updated_habit.periodicity, 'weekly')
        retrieved_habit = self.tracker.get_habit(habit_name)
        self.assertEqual(retrieved_habit.periodicity, 'weekly')

    def test_edit_habit_periodicity_invalid(self):
        """
        Test editing periodicity with an invalid value
        """
        habit_name = "Water Plants"
        self.tracker.create_habit(habit_name, 'daily')

        updated_habit = self.tracker.edit_habit(habit_name, new_periodicity='yearly')

        self.assertIsNotNone(updated_habit)
        self.assertEqual(updated_habit.periodicity, 'daily')
        retrieved_habit = self.tracker.get_habit(habit_name)
        self.assertEqual(retrieved_habit.periodicity, 'daily')

    # --- Test Listing Habits ---

    def test_list_all_habit_names_empty(self):
        """
        Test listing habits when none exist
        """
        names = self.tracker.list_all_habit_names()
        self.assertEqual(names, [])

    def test_list_all_habit_names_populated(self):
        """
        Test listing habits when some exist
        """
        names_to_create = ["Yoga", "Coding", "Planning"]
        for name in names_to_create:
            self.tracker.create_habit(name)

        listed_names = self.tracker.list_all_habit_names()
        self.assertEqual(len(listed_names), len(names_to_create))
        self.assertListEqual(sorted(listed_names), sorted(names_to_create))

    # --- Test Completion History ---

    @patch('tracker.date')
    def test_get_completion_history(self, mock_tracker_date):
        """
        Test retrieving completion history
        """
        habit_name = "Mindfulness"
        self.tracker.create_habit(habit_name, 'daily')

        dates_completed = [
            TODAY - timedelta(days=5),
            TODAY - timedelta(days=3),
            TODAY - timedelta(days=1)
        ]

        habit_id = self.tracker._get_habit_id(habit_name)
        for dt in dates_completed:
            self.tracker.cursor.execute(
                 "INSERT INTO completions (habit_id, completion_date) VALUES (?, ?)",
                 (habit_id, dt.isoformat())
            )
        self.tracker.db.conn.commit()

        mock_tracker_date.today.return_value = TODAY
        mock_tracker_date.fromisoformat.side_effect = date.fromisoformat
        self.tracker.record_completion(habit_name)

        history = self.tracker.get_completion_history(habit_name)

        expected_dates = sorted(dates_completed + [TODAY])
        self.assertEqual(len(history), len(expected_dates))
        self.assertListEqual(sorted(history), expected_dates)

    def test_get_completion_history_empty(self):
        """
        Test retrieving completion history for a habit with no completions
        """
        habit_name = "Singing"
        self.tracker.create_habit(habit_name, 'daily')
        history = self.tracker.get_completion_history(habit_name)
        self.assertEqual(history, [])


if __name__ == '__main__':
    unittest.main()
