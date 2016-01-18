from lifedashboard.redisvariable import RedisVariable
import lifedashboard.model as model
import lifedashboard.time as time
import isodate
import uuid
import pdb
import datetime

class BreakStatus:
    break_active = RedisVariable("break_active", int)
    break_start = RedisVariable("break_start", str)
    break_length = RedisVariable("break_length_min", int)
    break_end = RedisVariable("break_end", str)
    break_uuid = RedisVariable("break_uuid", str)
    break_type_id = RedisVariable("break_type_id", str)

    def __init__(self):
        return

    def startBreak(self, secretary, break_length, break_type):
        assert not self.break_active.value, "Cannot start a break that is active"
        tm = datetime.datetime.utcnow()
        self.break_active.value = 1
        self.break_start.value = self.writeDatetimeToString(datetime.datetime.utcnow())
        self.break_end.value = self.writeDatetimeToString(datetime.datetime.utcnow() + datetime.timedelta(seconds = 60 * break_length))
        self.break_length.value = break_length
        self.break_uuid.value = str(uuid.uuid4())
        self.break_type_id.value = break_type.id
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

    def clearState(self):
        self.break_active.value = 0
        self.break_start.value = ""
        self.break_length.value = 0
        self.break_end.value = ""
        self.break_uuid.value = ""
        self.break_type_id.value = ""
        return

    def endBreak(self, secretary):
        assert self.break_active, "Break must be active."
        self.break_active.value = 0

        activity_record = secretary.getActivityRecordFilename()

        start_time = time.convertUTCDTToLocal(isodate.parse_datetime(self.break_start.value))
        end_time = time.convertUTCDTToLocal(time.getUTCTime())

        start_time_str = time.formatTimeShort(start_time)
        end_time_str = time.formatTimeShort(end_time)

        activity_record = secretary.session.query(model.ActivityRecord).get(secretary.active_project.project_activityrecord_id.value)
        break_type = secretary.session.query(model.BreakActivity).get(self.break_type_id.value)
        line = "  Break: {}-{} - {}\n".format(start_time_str, end_time_str, break_type.name)
        for fn in [secretary.getActivityRecordFilename()]:

            with open(fn, 'a') as out_file:
                out_file.write(line)
                out_file.flush()

        breakobj = model.Break(start_time = start_time, end_time = end_time, break_activity = break_type, activity_record = activity_record)
        secretary.session.add(breakobj)
        secretary.session.commit()

        self.clearState()

        return
