from celery import Celery

BROKER = "redis://127.0.0.1:6379/0"

BACKEND = "redis://127.0.0.1:6379/1"
celery_app = Celery(
    "worker",
    broker=BROKER,
    backend=BACKEND,
    include=["ai_modules.tasks"],
)


celery_app.conf.update(
    task_serializer = "json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    result_expire=3000
)