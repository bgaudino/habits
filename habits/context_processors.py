import os

settings_module = os.environ['DJANGO_SETTINGS_MODULE']
if settings_module == 'habits.settings_production':
    env = 'production'
elif settings_module == 'habits.settings_staging':
    env = 'staging'
elif settings_module in ('habits.settings_dev', 'habits.settings_local'):
    env = 'dev'
elif settings_module == 'habits.settings_test':
    env = 'test'
else:
    env = None


def environment(request):
    return {'ENVIRONMENT': env}
