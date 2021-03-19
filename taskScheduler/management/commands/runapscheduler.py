import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.core.cache import cache
import time
import requests
from pymemcache.client.base import Client
from pymemcache import serde
client = Client('localhost', serde=serde.pickle_serde)


logger = logging.getLogger(__name__)

def requestBtcData():
    print("获取BTC数据")
    payload = {'start': '2010-07-17',
               'end': time.strftime("%Y-%m-%d", time.localtime())}
    r = requests.get(
        'https://api.coindesk.com/v1/bpi/historical/close.json', params=payload)
    json_data = r.json()
    client.set("btcData", json_data)
    return json_data

def requestBoxData():
    print("获取BOX数据")
    r = requests.get(
        'https://etf-api.b.watch/fund/f5ef6b5d-cc5a-3d90-b2c0-a2fd386e7a3c/line-charts?type=2')
    json_data = r.json()
    client.set('boxData', json_data)
    return json_data

def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            requestBoxData,
            # trigger=CronTrigger.from_crontab('1 0 * * *'),
            trigger=CronTrigger(second="*/10"),  # Every 10 seconds
            id="getBox",
            max_instances=1,
            replace_existing=True,
        )
        
        scheduler.add_job(
            requestBtcData,
            trigger=CronTrigger.from_crontab('1 0 * * *'),
            id="getBtc",
            max_instances=1,
            replace_existing=True,
        )

        # scheduler.add_job(requestBtcData, CronTrigger.from_crontab('8 8 * * *', timezone='UTC'), id="getBtcData", replace_existing=True,)
        # scheduler.add_job(requestBoxData, CronTrigger.from_crontab('10 16 * * *'), id="getBoxData", replace_existing=True,)

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
