from celery import Celery

app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',  # Redis broker
    backend='redis://localhost:6379/1'  # Natijalarni saqlash
)

app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
