from django.core.management.base import BaseCommand
import calendar
from datetime import datetime
from views import update_price_by_months  # Adjust the import based on your views location

class Command(BaseCommand):
    help = 'Updates prices by months only on the last day of the month'

    def handle(self, *args, **kwargs):
        today = datetime.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        
        if today.day == last_day:
            update_price_by_months(None)  # Simulating request argument as None for cron jobs
