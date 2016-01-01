import redis
import smtplib
from celery import Celery
import os

BROKER_URL = "redis://localhost:6379/0"
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  # 1 hour.
CELERY_RESULT_BACKEND = "redis+socket:///tmp/redis.sock"

app = Celery('secretary', broker=BROKER_URL)


# The notifier function
# Calling the function
# notify(title    = 'A Real Notification',
#        subtitle = 'with python',
#        message  = 'Hello, this is me, notifying you!',
#        sound = True,
#        temporary = True)
def notify(title, subtitle, message, sound = False, temporary = False):
    title = '-title {!r}'.format(title)
    sub = '-subtitle {!r}'.format(subtitle)
    msg = '-message {!r}'.format(message)
    sound = '-sound {}'.format("default") if sound else ""
    o = '-open http://www.google.com'
    sender = "-sender temporary" if temporary else ""
    os.system('terminal-notifier {}'.format(' '.join([msg, title, sub, sound, o, sender])))
    return

@app.task
def whisper(title, subtitle, message, parent_uuid = False):
    notify(title, subtitle, message, False, True)

@app.task
def say(title, subtitle, message, parent_uuid = False):
    notify(title, subtitle, message, True, True)

@app.task
def interrupt(title, subtitle, message, parent_uuid = False):
    notify(title, subtitle, message, True, False)

@app.task
def printMsg():
    notify(title    = 'A Real Notification',
           subtitle = 'with python',
           message  = 'Hello, this is me, notifying you!',
           sound = True,
           temporary = True)
    return

@app.task
def textSend(header, msg):

    # Credentials (if needed)
    # I recomend you create a new email account just for this
    username = 'secretary.alert'
    password = 'greystoke'
    fromaddr = 'secretary.alert@gmail.com'
    toaddrs  = '5102929383@vtext.com'

    text_msg = "{0}\n{1}".format(header, msg)

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, text_msg)
    server.quit()
    return





# interrupt.apply_async(countdown=10)
