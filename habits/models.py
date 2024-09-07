from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils import timezone


class HabitQuerySet(models.QuerySet):
    def with_streak_info(self, date):
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

    def current_streak(self):
        return self.streak_info[0]

    def streak_text(self):
        streak, on_the_line = self.streak_info
        if streak:
            if on_the_line:
                return f'{streak} day streak on the line!'
            return f'🎉 {streak} day{"s" if streak > 1 else ""} and counting!'
        return 'Start a new streak!'

    @cached_property
    def streak_info(self):
        streak = 0
        date = today = timezone.localdate()
        on_the_line = True
        last_date = None
        for completion in self.completion_set.all():
            if completion.date > today:
                continue
            if last_date == completion.date:
                continue
            last_date = completion.date
            if date == today:
                date -= timezone.timedelta(days=1)
                if completion.date == today:
                    on_the_line = False
                    streak += 1
                    continue
            if completion.date != date:
                break
            streak += 1
            date -= timezone.timedelta(days=1)
        return streak, on_the_line

    @cached_property
    def stats(self):
        stats = {p: {'completions': 0, 'days': d} for p, d in self.periods}
        today = timezone.localdate()
        days_since_first_completion = 0
        streaks = []
        streak = 0
        last_delta = None
        for i, completion in enumerate(self.completion_set.all(), 1):
            delta = today - completion.date
            if last_delta is None or last_delta.days == delta.days - 1:
                streak += 1
            else:
                streaks.append(streak)
                streak = 1
            for period, days in self.periods:
                if delta <= timezone.timedelta(days=days):
                    stats[period]['completions'] = i
            days_since_first_completion = delta.days
            last_delta = delta
        if streak:
            streaks.append(streak)
        print(streaks)
        days_since_creation = (today - self.date_created).days
        total_days = max(days_since_creation, days_since_first_completion)
        for period, days in self.periods:
            stats[period]['days'] = min(stats[period]['days'], total_days)
        stats['longest_streak'] = max(streaks) if streaks else 0
        return stats


class Completion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=False)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.habit.name}: {self.date}'
