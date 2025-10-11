import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configurações para Windows
app.conf.worker_pool = 'solo'  # Usa pool solo no Windows para evitar problemas
app.conf.worker_max_tasks_per_child = 100
app.conf.worker_prefetch_multiplier = 1

# Agendamento de tasks periódicas
app.conf.beat_schedule = {
    'check-critical-warnings-every-30-min': {
        'task': 'apps.emails.tasks.check_critical_warning_signs',
        'schedule': crontab(minute='*/30'),
    },
    'send-daily-alerts-summary': {
        'task': 'apps.emails.tasks.send_daily_alerts_summary',
        'schedule': crontab(hour=7, minute=0),  # Todos os dias às 7h
    },
}

app.conf.timezone = 'America/Sao_Paulo'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')