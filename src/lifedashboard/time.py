import datetime
import isodate
import pytz

def getUTCTime():
    return datetime.datetime.utcnow()

def getUTCIsoformatTimeStr():
    return getUTCTime().replace(second=0, microsecond=0).isoformat()

def convertUTCDTToLocal(dt, tz = 'America/Los_Angeles'):
    loc_tzinfo = pytz.timezone(tz)
    return dt.replace(tzinfo=pytz.utc).astimezone(loc_tzinfo)

def formatTimeShort(dt):
    # Jan 1 2016 2:30PM -> "1430"
    return dt.strftime("%H%M")

def formatTimeMed(dt):
    # Jan 1 2016 2:30PM -> "Tues 1430"
    return dt.strftime("%a %H%M")

def formatTimeLong(dt):
    # Jan 1 2016 2:30PM -> "JAN 10 Tue 1430"
    return dt.strftime("%b-%d %a %H%M")
