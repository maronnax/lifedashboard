# /usr/bin/sh

source /usr/local/bin/virtualenvwrapper.sh
workon lifedashboard
celery -A lifedashboard.tasks worker --loglevel=info -B -s /Users/naddy/Source/lifedashboard/db/celerybeat-schedule
