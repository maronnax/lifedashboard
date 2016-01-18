from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

BROKER_URL = "redis://localhost:6379/0"
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  # 1 hour.
CELERY_RESULT_BACKEND = "redis+socket:///tmp/redis.sock"
CELERY_TIMEZONE = 'America/Los_Angeles'

CELERYBEAT_SCHEDULE = {
    'wakeup-notification': {
        'task': 'lifedashboard.tasks.sendWakeupMessage',
        'schedule': crontab(minute='30', hour='7'),
        'args': ()
        },

    'start-day-notification': {
        'task': 'lifedashboard.tasks.startDay',
        'schedule': crontab(minute='25', hour = '8'),
        'args': ()
        },

    'end-day-notification': {
        'task': 'lifedashboard.tasks.endDay',
        'schedule': crontab(hour = '23', minute='45'),
        'args': ()
        }

    # 'print-every-30-seconds': {
    #     'task': 'lifedashboard.tasks.say',
    #     'schedule': timedelta(seconds=30),
    #     'args': ("test", "test", "test")
    # },

    # 'flip-value-every-30-seconds': {
    #     'task': 'lifedashboard.tasks.flip',
    #     'schedule': timedelta(seconds = 30)
    #     }
}

app = Celery('lifedashboard', broker=BROKER_URL)
app.conf.update(BROKER_TRANSPORT_OPTIONS = BROKER_TRANSPORT_OPTIONS)
app.conf.update(CELERYBEAT_SCHEDULE = CELERYBEAT_SCHEDULE)
app.conf.update(CELERY_TIMEZONE = CELERY_TIMEZONE)

# This causes errors.  Known issue with redis as a backend
# See this: https://github.com/celery/celery/blob/master/celery/backends/redis.py#L243
# app.conf.update(CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND)
