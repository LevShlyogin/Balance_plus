"""
Entrypoint для Celery Worker
"""
from app import celery_app

if __name__ == '__main__':
    celery_app.start()