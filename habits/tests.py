from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from . import models


User = get_user_model()


def streaks_from_completions(completion_dates):
    completion_dates = sorted(set(completion_dates), reverse=True)
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    completed_streaks = []
    missed_streaks = []
    win_streak = 1 if yesterday in completion_dates else 0
    last_date = yesterday
    for i in range(1, len(completion_dates)):
        current_date = completion_dates[i]
        delta = (last_date - current_date).days
        if delta == 0:
            continue
        elif delta == 1:
            win_streak += 1
        else:
            missed_streaks.append(delta - 1)
            completed_streaks.append(win_streak)
            win_streak = 1
        last_date = current_date
    if win_streak:
        completed_streaks.append(win_streak)

    return completed_streaks, missed_streaks


def get_day(num_days_ago):
    return datetime.today().date() - timedelta(days=num_days_ago)


class StatsTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(email='user@test.com')
        self.good_habit = models.Habit.objects.create(
            user=user,
            name='Good Habit',
        )
        self.good_habit.date_created = get_day(20)
        self.good_habit.save()
        self.bad_habit = models.Habit.objects.create(
            user=user,
            name='Bad Habit',
            is_bad=True,
        )
        self.bad_habit.date_created = get_day(20)
        self.bad_habit.save()
        for days in [
            1, 2, 3,
            6, 7, 8, 9, 10,
            12, 13,
            18,
        ]:
            models.Completion.objects.create(
                habit=self.good_habit,
                date=get_day(days),
            )
            models.Completion.objects.create(
                habit=self.bad_habit,
                date=get_day(days),
            )

    def get_day(self, num_days_ago):
        return datetime.today().date() - timedelta(days=num_days_ago)

    def test_streaks_good_habit(self):
        self.assertEqual(self.good_habit.streaks, [3, 5, 2, 1])

    def test_streaks_bad_habit(self):
        self.assertEqual(self.bad_habit.streaks, [2, 1, 4, 2])

    def test_longest_streak_good_habit(self):
        self.assertEqual(self.good_habit.longest_streak, 5)

    def test_longest_streak_bad_habit(self):
        self.assertEqual(self.bad_habit.longest_streak, 4)

    def test_current_streak_good_habit(self):
        self.assertEqual(self.good_habit.current_streak, 3)

    def test_current_streak_bad_habit(self):
        models.Completion.objects.all().delete()
        models.Completion.objects.create(
            habit=self.bad_habit,
            date=get_day(4)
        )
        self.assertEqual(self.bad_habit.current_streak, 3)

    def test_current_streak_good_habit_completed_today(self):
        models.Completion.objects.create(
            habit=self.good_habit,
            date=get_day(0),
        )
        self.assertEqual(self.good_habit.current_streak, 4)


class QuickStatsTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(email='user@test.com')
        self.bad_habit = models.Habit.objects.create(
            user=user,
            name='Bad Habit',
            is_bad=True,
        )
        self.bad_habit.date_created = get_day(20)
        self.bad_habit.save()
        for days in [
            4
        ]:
            models.Completion.objects.create(
                habit=self.bad_habit,
                date=get_day(days),
            )

    def test_bad_habit_streak(self):
        streak, completed_today = self.bad_habit.quick_stats
        self.assertEqual(streak, 3)
        self.assertFalse(completed_today)

    def test_bad_habit_streak_completed_yesterday(self):
        models.Completion.objects.create(
            habit=self.bad_habit,
            date=get_day(1),
        )
        streak, completed_today = self.bad_habit.quick_stats
        self.assertEqual(streak, 0)
        self.assertFalse(completed_today)

    def test_bad_habit_streak_completed_today(self):
        models.Completion.objects.create(
            habit=self.bad_habit,
            date=get_day(0),
        )
        streak, completed_today = self.bad_habit.quick_stats
        self.assertEqual(streak, 0)
        self.assertTrue(completed_today)
