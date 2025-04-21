from datetime import date, timedelta
from collections import defaultdict
import seaborn as sns
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta


class Analyse:
    def __init__(self, tracker):
        """
        :param tracker: Initialize analyse class with a tracker instance to access habit data
        """
        self.tracker = tracker
        sns.set_style("whitegrid")

    def get_completion_history(self, habit_name):
        """
        Fetches habit completion history a specified habit
        :param habit_name: Name of Habit
        :return: List of dates
        """
        return self.tracker.get_completion_history(habit_name)

    def calculate_daily_trend(self, habit_name, num_days=30):
        """
        Calculates daily completion trend over a specified number of days for daily habits
        :param habit_name: habit name
        :param num_days: specified days period
        :return: dictionary with date keys and bool values of 1 (completed) or 0 (not completed)
        """
        habit = self.tracker.get_habit(habit_name)
        if not habit:
            return {}

        history = self.get_completion_history(habit_name)
        end_date = date.today()
        start_date = end_date - timedelta(days=num_days - 1)
        trend = {}

        for day in (start_date + timedelta(n) for n in range(num_days)):
            trend[day] = 1 if day in history else 0
        return trend

    def calculate_weekly_trend(self, habit_name, num_weeks=4):
        """
        Calculates weekly completion trend over a specified number of weeks for weekly habits
        :param habit_name: habit name
        :param num_weeks: specified weeks period
        :return: dictionary with keys as week-start dates and values are number of completions that week.
        """
        habit = self.tracker.get_habit(habit_name)
        if not habit:
            return {}

        history = self.get_completion_history(habit_name)
        end_date = date.today()
        start_date = end_date - timedelta(weeks=num_weeks)
        trend = defaultdict(int)

        for completion_date in history:
            if start_date <= completion_date <= end_date:
                week_start = completion_date - timedelta(days=completion_date.weekday())
                trend[week_start] += 1
        return dict(trend)

    def calculate_monthly_trend(self, habit_name, num_months=3):
        """
        Calculates the monthly completion trend.
        Returns a dictionary where keys are month-start dates and values are the number of completions.
        """
        habit = self.tracker.get_habit(habit_name)
        if not habit:
            return {}
        history = self.get_completion_history(habit_name)
        end_date = date.today()

        first_day_current_month = date(end_date.year, end_date.month, 1)
        start_date = first_day_current_month - relativedelta(months=num_months)

        trend = defaultdict(int)

        expected_month_starts = set()
        current_month_start = start_date
        while current_month_start < first_day_current_month + relativedelta(months=1):
            expected_month_starts.add(current_month_start)
            trend[current_month_start] = 0
            current_month_start += relativedelta(months=1)

        for completion_date in history:
            if start_date <= completion_date <= end_date:
                month_start = date(completion_date.year, completion_date.month, 1)
                if month_start in expected_month_starts:
                    trend[month_start] += 1

        return dict(sorted(trend.items()))

    def visualize_daily_trend(self, habit_name, num_days=30):
        """
        :param habit_name: habit name
        :param num_days: specified days period
        :return: line plot of daily completion trend
        """
        trend_data = self.calculate_daily_trend(habit_name, num_days)
        if not trend_data:
            print(f"No daily trend data for '{habit_name}'.")
            return

        dates = list(trend_data.keys())
        completions = list(trend_data.values())

        plt.figure(figsize=(10, 6))
        sns.lineplot(x=dates, y=completions, marker='o')
        plt.title(f"Daily Completion Trend for '{habit_name}' (Last {num_days} Days)")
        plt.xlabel("Date")
        plt.ylabel("Completed (1) / Not Completed (0)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def visualize_weekly_trend(self, habit_name, num_weeks=4):
        """
        :param habit_name: habit name
        :param num_weeks: specified weeks period
        :return: bar plot of weekly completion trend
        """
        trend_data = self.calculate_weekly_trend(habit_name, num_weeks)
        if not trend_data:
            print(f"No weekly trend data for '{habit_name}'.")
            return

        week_starts = list(trend_data.keys())
        completion_counts = list(trend_data.values())

        plt.figure(figsize=(10, 6))
        sns.barplot(x=week_starts, y=completion_counts)
        plt.title(f"Weekly Completion Trend for '{habit_name}' (Last {num_weeks} Weeks)")
        plt.xlabel("Week Starting")
        plt.ylabel("Completions")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def visualize_monthly_trend(self, habit_name, num_months=3):
        """
        Generates a bar plot of the monthly completion trend.
        """
        trend_data = self.calculate_monthly_trend(habit_name, num_months)
        if not trend_data:
            print(f"No monthly trend data for '{habit_name}'.")
            return
        month_starts = list(trend_data.keys())
        completion_counts = list(trend_data.values())

        plt.figure(figsize=(10, 6))
        sns.barplot(x=month_starts, y=completion_counts)
        plt.title(f"Monthly Completion Trend for '{habit_name}' (Last {num_months} Months)")
        plt.xlabel("Month Starting")
        plt.ylabel("Completions")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
