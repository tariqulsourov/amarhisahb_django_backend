import json
import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.signing import Signer
from pywebpush import webpush, WebPushException

from account.models import PushSubscription, UsersSettings
from account.vapid import VAPID_PRIVATE_KEY_PATH, ensure_vapid_keys
from savings.models import ScheduledTransaction

class Command(BaseCommand):
    help = 'Process planned scheduled transactions and send push notifications with action triggers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sending reminders regardless of the date constraints',
        )

    def handle(self, *args, **options):
        force = options['force']
        dhaka_tz = pytz.timezone('Asia/Dhaka')
        now_dhaka = timezone.now().astimezone(dhaka_tz)
        today_date = now_dhaka.date()
        current_time_str = now_dhaka.strftime('%H:%M')

        # Find pending transactions scheduled for today or earlier that haven't been notified yet today
        if force:
            scheduled_items = ScheduledTransaction.objects.filter(status='pending')
        else:
            scheduled_items = ScheduledTransaction.objects.filter(
                status='pending',
                scheduled_date__lte=today_date
            ).exclude(last_notified_date=today_date)

        self.stdout.write(f"Processing scheduled transactions for Dhaka date: {today_date} {current_time_str} (Count: {scheduled_items.count()})")

        sent_count = 0
        signer = Signer()
        ensure_vapid_keys()

        for item in scheduled_items:
            user = item.user

            # Check user reminder time preference (defaults to 09:00 if not set)
            setting = UsersSettings.objects.filter(user=user).first()
            target_time = (setting.reminder_time if setting and setting.reminder_time else '09:00')
            if not force and current_time_str < target_time:
                self.stdout.write(f"Item {item.id} scheduled for {user.email}, waiting until {target_time} (current: {current_time_str}). Skipping.")
                continue

            subscriptions = PushSubscription.objects.filter(user=user)

            if not subscriptions.exists():
                self.stdout.write(f"Transaction {item.id} has no registered subscriptions for user {user.email}")
                continue

            # Generate pre-signed URL approval token
            signed_token = signer.sign(item.id)
            approve_url = f"/api/v1/scheduled-transactions/{item.id}/approve/?token={signed_token}"
            
            # Target redirect page URL
            target_page = "/costs" if item.transaction_type == 'cost' else "/incomes"
            redirect_url = f"{target_page}?plannedId={item.id}"

            payload = {
                "title": f"Amar Hishab: Planned {item.transaction_type.capitalize()}",
                "body": f"Log planned {item.transaction_type}: {item.description or 'No notes'} of ৳ {item.amount.toLocaleString() if hasattr(item.amount, 'toLocaleString') else item.amount} from {item.wallet.wallet_name}?",
                "url": redirect_url,
                "approveUrl": approve_url,
                "actions": [
                    {"action": "approve", "title": "Approve & Log", "icon": "/icon-192.png"},
                    {"action": "edit", "title": "Review & Edit", "icon": "/icon-192.png"}
                ]
            }

            self.stdout.write(f"Sending push for planned item {item.id} (Amount: {item.amount}) to {user.email}...")

            item_notified = False
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
                    item_notified = True
                except WebPushException as ex:
                    self.stdout.write(self.style.WARNING(f"Push failed for endpoint {sub.endpoint[:30]}... status: {ex.response.status_code if ex.response else 'unknown'}"))
                    if ex.response is not None and ex.response.status_code in [404, 410]:
                        sub.delete()
                        self.stdout.write(self.style.WARNING(f"Deleted expired subscription for {user.email}"))

            if item_notified and not force:
                item.last_notified_date = today_date
                item.save(update_fields=['last_notified_date'])

        self.stdout.write(self.style.SUCCESS(f"Finished processing scheduled transactions. Sent notifications: {sent_count}"))
