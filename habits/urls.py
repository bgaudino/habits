import django.views.static
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path, register_converter
from django.views.generic import TemplateView

from . import views
from .converters import DateConverter


register_converter(DateConverter, 'date')

urlpatterns = [
    path(
        'robots.txt',
        TemplateView.as_view(
            template_name='robots.txt',
            content_type='text/plain',
        ),
    ),
    path('admin/', admin.site.urls),
    path('', views.HabitListView.as_view(), name='habit_list'),
    path('<int:pk>/', views.HabitDetailView.as_view(), name='habit_detail'),
    path('create/', views.HabitCreateView.as_view(), name='habit_create'),
    path(
        'complete/<int:pk>/<date:date>/',
        views.ToggleCompletionView.as_view(),
        name='toggle_completion',
    ),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', django.views.static.serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
