from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from huami.models import HealthData, HuamiAccount

def my_job():
  users = HuamiAccount.objects.all()
  for user in users:
    HealthData.create_from_sync_data(user)


class Command(BaseCommand):
  help = "Runs APScheduler."

  def handle(self, *args, **options):
    scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
      my_job,
      trigger=CronTrigger(hour="00", minute="00"),  # Every 10 seconds
      id="updateHealth",  # The `id` assigned to each job MUST be unique
      max_instances=1,
      replace_existing=True,
    )

    try:
      scheduler.start()
    except KeyboardInterrupt:
      scheduler.shutdown()