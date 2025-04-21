from datetime import date, timedelta


class Habit:
    def __init__(self, name, periodicity='daily', streak=0, last_completed=None, streak_saves=0, longest_streak=0):
        self.name = name
        self.periodicity = periodicity
        self.streak = streak
        self.last_completed = last_completed
        self.streak_saves = streak_saves
        self.longest_streak = longest_streak

    def change_periodicity(self, new_periodicity):
        """
        Change the periodicity of a specified habit to daily, weekly or monthly
        :param new_periodicity: new periodicity
        """
        if new_periodicity in ['daily', 'weekly', 'monthly']:
            self.periodicity = new_periodicity
            print(f"Periodicity for '{self.name}' updated to '{new_periodicity}'.")
        else:
            print("Invalid periodicity. Please choose 'daily', 'weekly', or 'monthly'.")

    def get_period_delta(self):
        """
        Gets the time difference of completions based on periodicity.
        Periodicity has default of daily
        """
        if self.periodicity == 'daily':
            return timedelta(days=1)
        elif self.periodicity == 'weekly':
            return timedelta(weeks=1)
        elif self.periodicity == 'monthly':
            return timedelta(days=30)
        return timedelta(days=1)

    def streak_reset(self):
        """
        Resets habit streak if habit has not been completed within the specified period
        """
        if self.last_completed:
            time_elapsed = date.today() - self.last_completed
            period_delta = self.get_period_delta()
            if time_elapsed > period_delta:
                self.streak = 0
                print(f"Streak for '{self.name}' reset. Last completed on {self.last_completed}")

    def increment(self):
        """
        Increments streak when a new date has been logged within the chosen habit period.
        It also updates the longest streak
        """
        today = date.today()
        if self.last_completed is None or (today - self.last_completed) >= self.get_period_delta():
            self.streak += 1
            self.last_completed = today
            if self.streak > self.longest_streak:
                self.longest_streak = self.streak
            print(f"Streak for '{self.name}' updated to {self.streak}. Completed today: {today}")
        else:
            print(f"'{self.name}' already completed.")

    def streak_save(self):
        """
        A streak save in case there were unavoidable circumstances that lead
        to missing a habit completion, e.g., an emergency.
        """
        if self.streak_saves > 0:
            self.streak_saves -= 1
            self.last_completed = date.today()
            print(f"Streak saved for '{self.name}'. Streak is still {self.streak}. "
                  f"Streak saves remaining: {self.streak_saves}.")
        else:
            print(f"No streak saves available for '{self.name}'.")
