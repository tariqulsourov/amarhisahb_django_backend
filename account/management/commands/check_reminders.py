import json
import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from pywebpush import webpush, WebPushException

from account.models import UsersSettings, PushSubscription
from account.vapid import VAPID_PRIVATE_KEY_PATH, ensure_vapid_keys
from costs.models import Costs
from income.models import Incomes

class Command(BaseCommand):
    help = 'Check user settings and send Web Push reminders if no inputs are entered for today'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending reminders regardless of the scheduled time or daily inputs check',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send a direct test reminder to all active subscriptions of the specified email',
        )

    def handle(self, *args, **options):
        force = options['force']
        test_email = options['test_email']

        # Determine target settings
        if test_email:
            settings_qs = UsersSettings.objects.filter(user__email=test_email)
            self.stdout.write(self.style.NOTICE(f"Testing reminders for email: {test_email}"))
        else:
            settings_qs = UsersSettings.objects.filter(reminder_enabled=True)

        # Use Bangladesh Standard Time (Asia/Dhaka) for user-facing schedule matching
        dhaka_tz = pytz.timezone('Asia/Dhaka')
        now = timezone.now().astimezone(dhaka_tz)
        current_time_str = now.strftime('%H:%M')
        today_date = now.date()

        self.stdout.write(f"Running check_reminders at Dhaka time: {now} (Time: {current_time_str}, Date: {today_date})")

        payload = {
            "title": "Amar Hishab Daily Reminder",
            "body": "You haven't logged any transactions today! Tap here to quickly log an expense.",
            "url": "/costs?openAddModal=true"
        }

        sent_count = 0
        ensure_vapid_keys()

        for setting in settings_qs:
            user = setting.user

            # If not testing specifically, check catch-up window
            if not force and not test_email:
                # 1. Skip if already sent today
                if setting.last_reminder_sent_date == today_date:
                    continue

                # 2. Check if current time has reached or passed user's scheduled time
                user_time = setting.reminder_time or '21:00'
                if current_time_str < user_time:
                    continue

            # If not forced, check if the user already logged cost/income today
            if not force and not test_email:
                has_cost = Costs.objects.filter(cost_related_id__create_by=user, cost_date=today_date).exists()
                has_income = Incomes.objects.filter(income_related_id__create_by=user, income_date=today_date).exists()
                if has_cost or has_income:
                    self.stdout.write(f"User {user.email} already entered data today. Skipping.")
                    continue

            subscriptions = PushSubscription.objects.filter(user=user)
            if not subscriptions.exists():
                self.stdout.write(f"User {user.email} has reminders enabled but no registered device subscriptions.")
                continue

            self.stdout.write(f"Sending push reminder to {user.email} ({subscriptions.count()} device subscription(s))...")

            user_notified = False
            for sub in subscriptions:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub.endpoint,
                            "keys": {
                                "p256dh": sub.p256dh,
                                "auth": sub.auth
                            }
                        },
                        data=json.dumps(payload),
                        vapid_private_key=VAPID_PRIVATE_KEY_PATH,
                        vapid_claims={"sub": f"mailto:{user.email}"}
                    )
                    sent_count += 1
                    user_notified = True
                except WebPushException as ex:
                    self.stdout.write(self.style.WARNING(f"Push failed for subscription on endpoint {sub.endpoint[:30]}... status: {ex.response.status_code if ex.response else 'unknown'}"))
                    if ex.response is not None and ex.response.status_code in [404, 410]:
                        sub.delete()
                        self.stdout.write(self.style.WARNING(f"Deleted expired/invalid subscription for {user.email}"))

            if user_notified and not test_email:
                setting.last_reminder_sent_date = today_date
                setting.save(update_fields=['last_reminder_sent_date'])

        self.stdout.write(self.style.SUCCESS(f"Finished check_reminders task. Total notifications sent: {sent_count}"))
