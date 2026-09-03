from django.core.management.base import BaseCommand
import time
import datetime

class Command(BaseCommand):
    help = 'Run a task at the last minute of the last day of the month'

    def handle(self, *args, **kwargs):
        while True:
            now = datetime.datetime.now()
          
            self.stdout.write(self.style.SUCCESS('Task executed successfully'))
            print('tessdfsdfasfsaf')
            
            # Sleep for one minute before checking again
            time.sleep(60)