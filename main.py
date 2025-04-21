import click
from tracker import Tracker
from analyse import Analyse
from datetime import datetime
import sqlite3

# Initialize the tracker and analyzer
tracker = Tracker()
analyzer = Analyse(tracker)


def get_habit_name(prompt="Enter habit name"):
    """
    Get habit name with validation
    :param prompt: habit name to be entered
    :return: habit
    """
    habit_name = click.prompt(prompt, type=str)
    if not tracker.get_habit(habit_name):
        raise click.ClickException(f"Habit '{habit_name}' not found.  Please create the habit first.")
    return habit_name


def get_date(prompt="Enter date (YYYY-MM-DD)"):
    """
    Get date with validation
    :param prompt: date of completion to be entered
    :return: date of habit completion
    """
    date_str = click.prompt(prompt, type=str)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise click.ClickException("Invalid date format. Please use YYYY-MM-DD.")


@click.group()
def cli():
    """Habit Tracker CLI"""
    pass


@cli.command()
def list_habits():
    """
    List all habits
    :return: lists all habits
    """
    habit_names = tracker.list_all_habit_names()
    if habit_names:
        click.echo("Current habits:")
        for name in habit_names:
            click.echo(f"- {name}")
    else:
        click.echo("No habits found or unable to retrieve habits.")


@cli.command()
@click.argument('name', type=str)
@click.option('--periodicity', type=click.Choice(['daily', 'weekly', 'monthly']),
              default='daily', help='Periodicity of the habit')
def create(name, periodicity):
    """
    Create new habit
    :param name: name of the new habit
    :param periodicity: periodicity of the new habit, i.e., daily, weekly, or monthly
    """
    habit = tracker.create_habit(name, periodicity)
    if habit:
        click.echo(f"Habit '{habit.name}' created with periodicity '{habit.periodicity}'.")


@cli.command()
def list_habits():
    """
    List all habits.
    :return: prints list of existing habits
    """
    habits = tracker.cursor.execute("SELECT name FROM habits").fetchall()
    if habits:
        click.echo("Current habits:")
        for habit_name in habits:
            click.echo(f"- {habit_name[0]}")
    else:
        click.echo("No habits created yet.")


@cli.command()
@click.argument('name', type=str)
@click.option('--new-name', prompt="Enter new name for the habit", type=str)
def edit_name(name, new_name):
    """
    Edit the name of an existing habit
    :param name: name of the habit
    :param new_name: new name of the habit
    :return: updated name of the existing habit
    """
    updated_habit = tracker.edit_habit(name, new_name=new_name)
    if updated_habit:
        click.echo(f"Habit '{name}' renamed to '{updated_habit.name}'.")


@cli.command()
@click.argument('name', type=str)
@click.option('--new-periodicity', prompt="Enter new periodicity (daily, weekly, monthly)",
              type=click.Choice(['daily', 'weekly', 'monthly']))
def edit_periodicity(name, new_periodicity):
    """
    Edit the periodicity of an existing habit
    :param name: name of the habit
    :param new_periodicity: new periodicity of the specified habit
    :return: updated periodicity of the existing habit
    """
    updated_habit = tracker.edit_habit(name, new_periodicity=new_periodicity)
    if updated_habit:
        click.echo(f"Periodicity for habit '{updated_habit.name}' updated to '{updated_habit.periodicity}'.")


@cli.command()
@click.argument('name', type=str)
def delete(name):
    """
    Delete a specified habit
    :param name: name of the habit
    """
    tracker.delete_habit(name)


@cli.command()
@click.argument('name', type=str)
def record_completion(name):
    """
    Record a completion for a specified habit
    :param name: name of the habit
    """
    try:
        habit = tracker.get_habit(name)
        if not habit:
            click.echo(f"Error: Habit '{name}' not found.")
            return

        tracker.record_completion(name)

    except sqlite3.Error as db_err:
        click.echo(f"Database error during completion recording: {db_err}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")


@cli.command()
@click.argument('name', type=str)
def show_streak(name):
    """
    Shows the current streak of a specified habit
    :param name: name of the habit
    :return: current streak of the specified habit
    """
    habit = tracker.get_habit(name)
    if habit:
        click.echo(f"Current streak for habit '{habit.name}': {habit.streak} days.")
    else:
        click.echo(f"Habit '{name}' not found.")


@cli.command()
@click.argument('name', type=str)
def show_longest_streak(name):
    """
    Show the longest streak for a specified habit
    :param name: name of the habit
    :return: longest streak of the specified habit
    """
    habit = tracker.get_habit(name)
    if habit:
        click.echo(f"Longest streak for habit '{habit.name}': {habit.longest_streak} days.")
    else:
        click.echo(f"Habit '{name}' not found.")


@cli.command()
@click.argument('name', type=str)
def show_daily_trend(name):
    """
    Show the daily trend for a specified habit
    :param name: name of the habit
    :return: a graph to show the daily habit's completion trends
    """
    analyzer.visualize_daily_trend(name, num_days=7)


@cli.command()
@click.argument('name', type=str)
def show_weekly_trend(name):
    """
    Show the weekly trend for a specified habit
    :param name: name of the habit
    :return: a graph to show the weekly habit's completion trends
    """
    analyzer.visualize_weekly_trend(name, num_weeks=4)


@cli.command()
@click.argument('name', type=str)
@click.option('--num_months', type=int, default=3, help='Number of months to show')
def show_monthly_trend(name, num_months):
    """
    Show the monthly trend for a specified habit
    :param name: name of the habit
    :param num_months: number of months
    :return: a graph to show the monthly habit's completion trends
    """
    analyzer.visualize_monthly_trend(name, num_months)


if __name__ == '__main__':
    cli()
    tracker.close_connection()
