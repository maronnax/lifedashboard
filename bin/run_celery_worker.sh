# /usr/bin/sh

source /usr/local/bin/virtualenvwrapper.sh
workon lifedashboard
celery -A lifedashboard.tasks worker --loglevel=info
