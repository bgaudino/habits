from django import forms
from django.urls import reverse_lazy

from . import models


class DateForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(
        attrs={
            'hx-get': reverse_lazy('habit_list'),
            'hx-trigger': 'change',
            'hx-target': '#habit-list',
            'hx-select': '#habit-list',
            'hx-swap': 'outerHTML',
            'hx-push-url': 'true',
        }
    ))


class HabitForm(forms.ModelForm):
    class Meta:
        model = models.Habit
        fields = ['name']
