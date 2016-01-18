from lifedashboard.settings import app
from IPython import embed
import redis
from lifedashboard.config import AppConfigParser
from lifedashboard.secretary.variable.dayactive import DayActive
import smtplib
import os
import lifedashboard.secretary.variable.active as active
from lifedashboard.tools import getApplicationConfigFile
import lifedashboard.secretary.variable.breakstatus as breakstatus
from datetime import timedelta
import smsmessenger.smsmessenger as smsmessenger
import pdb

config_fn = getApplicationConfigFile()
config = AppConfigParser()
config.read(getApplicationConfigFile())

section_name = "smsmessenger"

USERNAME = config.get("username", section_name)
PASSWORD = config.get("password", section_name)
FROMADDR = config.get("fromaddr", section_name)
TOADDRS  = config.get("toaddrs", section_name)
SMTP_SERVER = config.get("smtp_server", section_name)
RECIEVE_PORT = config.get("recieve_port", section_name, type=int)
SEND_PORT = config.get("send_port", section_name, type=int)
MESSAGE_INTERVAL = config.get("message_interval", section_name)

smsmessenger.setupModule(username = USERNAME,
                         password = PASSWORD,
                         fromaddrs = FROMADDR,
                         toaddrs = TOADDRS,
                         smtp_server = SMTP_SERVER,
                         recieve_port = RECIEVE_PORT,
                         send_port = SEND_PORT,
                         message_interval = MESSAGE_INTERVAL)

@app.task
def flip():
    day_active = DayActive()
    val = day_active.value
    if val != 0:
        day_active.value = 0
    else:
        day_active.value = 1

    return

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

def checkIDIsActive(uuid):
    return (uuid == active.ActiveProject.project_uuid.value or \
            uuid == active.ActivePomodoro.pomodoro_uuid.value or \
            uuid == breakstatus.BreakStatus.break_uuid.value)

@app.task
def whisper(title, subtitle, message, parent_uuid = False):
    if parent_uuid and not checkIDIsActive(parent_uuid):
        # notify("Message cancelled {}".format(title),
        #        "Message cancelled - {}".format(subtitle),
        #        "Message cancelled - {} - {}".format(message, parent_uuid))
        pass
    else:
        notify(title, subtitle, message, False, True)
    return

@app.task
def phoneAlert(title, subtitle, message, parent_uuid = False):
    # Credentials (if needed)
    # I recomend you create a new email account just for this

    username = 'secretary.alert'
    password = 'greystoke'
    fromaddr = 'secretary.alert@gmail.com'
    toaddrs  = '5102929383@vtext.com'

    text_msg = "{0}\n{1}\n{2}".format(title, subtitle, message)

    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, text_msg)
    server.quit()
    return

@app.task
def say(title, subtitle, message, parent_uuid = False):

    if parent_uuid and not checkIDIsActive(parent_uuid):
        # notify("Message cancelled {}".format(title),
        #        "Message cancelled - {}".format(subtitle),
        #        "Message cancelled - {} - {}".format(message, parent_uuid))
        pass
    else:
        notify(title, subtitle, message, True, True)

@app.task
def interrupt(title, subtitle, message, parent_uuid = False):
    if parent_uuid and not checkIDIsActive(parent_uuid):
        # notify("Message cancelled {}".format(title),
        #        "Message cancelled - {}".format(subtitle),
        #        "Message cancelled - {} - {}".format(message, parent_uuid))
        pass
    else:
        notify(title, subtitle, message, True, False)


@app.task
def yell(title, subtitle, message, parent_uuid = False):
    if parent_uuid and not checkIDIsActive(parent_uuid):
        # notify("Message cancelled {}".format(title),
        #        "Message cancelled - {}".format(subtitle),
        #        "Message cancelled - {} - {}".format(message, parent_uuid))
        pass
    else:
        smsmessenger.sendTextMessage(title + '\n' + subtitle + '\n' + message)
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
def sendWakeupMessage():
    yell("Time to wakeup", "Please wakeup", "Time to wakeup.")
    return

@app.task
def startDay():
    yell("Time to start your work day", "Time to start work in 5 minutes", "Please don't let the day fritter away.")
    return

@app.task
def endDay():
    yell("Time for Bed.", "Time to put things away, brush your teeth, and go to bed.", "Going to sleep early is one of the most important things you can do to make your work and life go smoothly.")
    return


# interrupt.apply_async(countdown=10)
