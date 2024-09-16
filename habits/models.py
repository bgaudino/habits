from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils import timezone


class HabitQuerySet(models.QuerySet):
    def with_completion_status(self, date):
        return self.prefetch_related(
            models.Prefetch(
                'completion_set',
                queryset=Completion.objects.order_by('-date'),
            )
        ).annotate(
            is_completed=models.Exists(
                Completion.objects.filter(
                    habit=models.OuterRef('pk'),
                    date=date,
                )
            )
        )


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255, unique=True)
    date_created = models.DateField(auto_now_add=True)
    is_bad = models.BooleanField(default=False)

    objects = HabitQuerySet.as_manager()

    periods = (('year', 365), ('month', 30), ('week', 7))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'is_completed'):
            self.is_completed = self._is_completed

    def __str__(self):
        return self.name

    def toggle_completion(self, date=None):
        date = date or timezone.localdate()
        if self.is_completed:
            self.completion_set.filter(date=date).delete()
        else:
            self.complete(date)
        return self

    def complete(self, date=None):
        date = date or timezone.localdate()
        return Completion.objects.create(habit=self, date=date)

    def uncomplete(self, date=None):
        date = date or timezone.localdate()
        self.completion_set.filter(date=date).delete()

    def _is_completed(self, date):
        return self.completion_set.filter(date=date).exists()

    @property
    def streaks(self):
        return self.stats['loss_streaks'] if self.is_bad else self.stats['win_streaks']

    @property
    def current_streak(self):
        if hasattr(self, 'stats'):
            return self.stats['current_streak']
        return self.quick_stats[0]

    @property
    def longest_streak(self):
        return max(self.streaks) if self.streaks else 0

    @property
    def completed_today(self):
        if hasattr(self, 'stats'):
            return self.stats['completed_today']
        return self.quick_stats[1]

    def streak_text(self):
        if self.current_streak == 0:
            if self.is_bad and self.completed_today:
                return '🌅 Tomorrow is a new day'
            return '🌱 Start a new streak!'
        elif self.completed_today:
            return f'🎉 {self.current_streak} day{"s" if self.current_streak > 1 else ""} and counting!'
        else:
            return f'⏳ {self.current_streak} day streak on the line!'

    @cached_property
    def stats(self):
        stats = {p: {'completions': 0, 'days': d} for p, d in self.periods}
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)
        completed_streaks = []
        missed_streaks = []
        win_streak = 0
        completed_today = False
        completed_yesterday = False
        last_date = yesterday
        for completion in self.completion_set.all():
            current_date = completion.date
            if current_date == today:
                completed_today = True
                continue
            delta = (last_date - current_date).days
            for period, days in self.periods:
                if 0 <= (yesterday - current_date).days < days:
                    stats[period]['completions'] += 1
            if current_date == yesterday:
                completed_yesterday = True
                win_streak = 1
                continue
            elif delta == 1 and (completed_yesterday or last_date != yesterday):
                win_streak += 1
            else:
                if last_date == yesterday and not completed_yesterday:
                    missed_streaks.append(delta)
                else:
                    missed_streaks.append(delta - 1)
                completed_streaks.append(win_streak)
                win_streak = 1
            last_date = current_date
        if win_streak:
            completed_streaks.append(win_streak)
        start_date = min(self.date_created, last_date)
        delta = (last_date - start_date).days
        if delta > 1:
            missed_streaks.append(delta)
        total_days = (yesterday - start_date).days + 1
        for period, days in self.periods:
            stats[period]['days'] = min(days, total_days)
        stats['win_streaks'] = completed_streaks
        stats['loss_streaks'] = missed_streaks
        stats['completed_today'] = completed_today
        stats['completed_yesterday'] = completed_yesterday
        current_streak = 0
        if self.is_bad:
            if not completed_today or completed_yesterday:
                current_streak = missed_streaks[0] if missed_streaks else 0
        else:
            if completed_today:
                if completed_yesterday:
                    completed_streaks[0] += 1
                else:
                    completed_streaks.insert(0, 1)
                current_streak = completed_streaks[0]
            elif completed_yesterday:
                current_streak = completed_streaks[0]
        stats['current_streak'] = current_streak
        return stats

    @cached_property
    def quick_stats(self):
        streak = 0
        date = today = timezone.localdate()
        completion = self.completion_set.first()
        completed_today = completion and completion.date == today
        if self.is_bad:
            start = completion.date if completion else self.date_created
            streak = (today - start).days
            return streak - 1, completed_today

        last_date = None
        for completion in self.completion_set.all():
            start = completion.date
            if completion.date > today:
                continue
            if last_date == completion.date:
                continue
            last_date = completion.date
            if date == today:
                date -= timezone.timedelta(days=1)
                if completion.date == today:
                    streak += 1
                    continue
            if completion.date != date:
                break
            streak += 1
            date -= timezone.timedelta(days=1)
        return streak, completed_today


class Completion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.habit.name}: {self.date}'
