from lifedashboard.redisvariable import RedisVariable
import datetime

class BreakStatus:
    break_active = RedisVariable("break_active", int)
    break_start = RedisVariable("break_start", str)
    break_length = RedisVariable("break_length_min", int)
    break_end = RedisVariable("break_end", str)

    def __init__(self):
        return

    def startBreak(self, break_length = 5):
        assert not self.break_active.value, "Cannot start a break that is active"
        tm = datetime.datetime.utcnow()
        self.break_active.value = 1
        self.break_start.value = self.writeDatetimeToString(datetime.datetime.utcnow())
        self.break_end.value = self.writeDatetimeToString(datetime.datetime.utcnow() + datetime.timedelta(seconds = 60 * break_length))
        self.break_length.value = break_length
        return

    def __repr__(self):
        if not self.break_active.value:
            return "Not active"
        else:
            break_string = self.break_end.value
            break_dt = self.parseDatetimeFromString(break_string)
            break_fin_string = self.getTimeStringFromVar(break_dt)
            return "Active: Ends at {}".format()

    on_break = property(lambda cls : cls.break_active.value)

    def getTimeStringFromVar(self, dt):
        return self.parseDatetimeFromString(dt).strftime("%H%M")

    def writeDatetimeToString(self, dt):
        return dt.replace(second=0, microsecond=0).isoformat()

    def parseDatetimeFromString(self, string):
        if string:
            return isodate.parse_date(string)
        else:
            return datetime.datetime(1970,1,1)

    def endBreak(self):
        assert self.break_active, "Break must me active."
        self.break_active.value = 0
        self.break_start.value = ""
        self.break_length.value = 0
        self.break_end.value = ""
        return
