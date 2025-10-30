import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('karu')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Agendamento das tasks
app.conf.beat_schedule = {
    'check-weight-loss-every-6h': {
        'task': 'apps.email.tasks.check_weight_loss_alerts',
        'schedule': crontab(hour='*/6'),  # A cada 6 horas
    },
    'check-missed-appointments-daily': {
        'task': 'apps.email.tasks.check_missed_appointments', 
        'schedule': crontab(hour=9, minute=0),  # Todos os dias às 9h
    },
    'send-pending-alerts-every-30min': {
        'task': 'apps.email.tasks.send_pending_alerts',
        'schedule': crontab(minute='*/30'),  # A cada 30 minutos
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')