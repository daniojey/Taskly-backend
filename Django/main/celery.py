# main/celery.py

import os
import sys
from celery import Celery
from celery.signals import worker_process_init, task_postrun
from django.db import connections

# Добавьте путь к Django проекту
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

app = Celery('main')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

@worker_process_init.connect
def close_db_connections(**kwargs):
    connections.close_all()

@task_postrun.connect
def close_db_after_task(**kwargs):
    connections.close_all()