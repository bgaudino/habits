import urllib.parse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, View, CreateView, DetailView

from .forms import DateForm, HabitForm
from .models import Habit


class HabitListView(LoginRequiredMixin, ListView):
    def setup(self, request, *args, **kwargs):
        self.date = self.get_date(request)
        if self.date > timezone.localdate():
            raise Http404
        return super().setup(request, *args, **kwargs)

    def get_date(self, request):
        form = DateForm(request.GET)
        if form.is_valid():
            return form.cleaned_data['date']
        else:
            return timezone.localdate()

    def get_queryset(self):
        return Habit.objects.filter(
            user=self.request.user
        ).with_completion_status(self.date)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['habit_form'] = HabitForm()
        context['date'] = self.date
        context['date_form'] = DateForm(initial={'date': self.date})
        context['prev_date'] = self.date - timezone.timedelta(days=1)
        if self.date < timezone.localdate():
            context['next_date'] = self.date + timezone.timedelta(days=1)
        return context


class ToggleCompletionView(LoginRequiredMixin, View):
    def get_habit(self):
        return get_object_or_404(
            self.request.user.habit_set.with_completion_status(self.kwargs['date']),
            pk=self.kwargs['pk'],
        )

    def post(self, request, pk, date):
        habit = self.get_habit()
        habit.toggle_completion(date)
        habit = self.get_habit()
        return render(
            request,
            'habits/partials/_habit.html',
            {'habit': habit, 'date': date}
        )


class HabitCreateView(LoginRequiredMixin, CreateView):
    form_class = HabitForm
    success_url = reverse_lazy('habit_list')
    template_name = 'habits/habit_list.html'

    def form_invalid(self, form):
        content = render_to_string(
            'habits/partials/_habit_form.html',
            {'habit_form': form, 'open': True},
            self.request,
        )
        return HttpResponse(
            content=content,
            headers={'HX-Retarget': '#add-form', 'HX-Reselect': '#add-form'}
        )

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        url = super().get_success_url()
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            query = urllib.parse.urlparse(referer).query
            if query:
                url += f'?{query}'
        return url


class HabitDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return self.request.user.habit_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = self.object.stats
        return context
