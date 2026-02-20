"""
Management command to run Celery worker.
"""
from django.core.management.base import BaseCommand
from celery import Celery
from celery.bin import worker


class Command(BaseCommand):
    help = 'Run Celery worker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            default='info',
            help='Log level'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='Number of concurrent workers'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Celery worker...'))
        
        app = Celery('salahtime')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        worker_cmd = worker.worker(app=app)
        options = {
            'loglevel': options['loglevel'],
            'concurrency': options['concurrency'],
            'pool': 'prefork',
        }
        
        worker_cmd.run(**options)

