import redis
import isodate
import datetime
import lifedashboard.model as model # BLECK!

class RedisActiveRecord:
    @staticmethod
    def getRedis():
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        return r

    @classmethod
    def getTimeStr(cls):
        return datetime.datetime.utcnow().replace(second=0, microsecond=0).isoformat()

class ActivePomodoro(RedisActiveRecord):
    @classmethod
    def showState(cls):
        r = cls.getRedis()
        print("pomodoro_active: {}".format(r.get("pomodoro_active")))
        print("pomodoro_start_time: {}".format(r.get("pomodoro_start_time")))
        print("pomodoro_end_time: {}".format(r.get("pomodoro_end_time")))
        print("pomodoro_message: {}".format(r.get("pomodoro_message")))
        return

    @classmethod
    def clearState(cls):
        r = cls.getRedis()
        r.delete("pomodoro_active")
        r.delete("pomodoro_start_time")
        r.delete("pomodoro_end_time")
        r.delete("pomodoro_message")
        r.set("pomodoro_active", 0)
        return

    @classmethod
    def startActivePomodoro(cls):
        assert ActiveProject.projectIsActive(), "Project must be active to start a pomodoro."
        assert not cls.pomodoroIsActive(), "Pomodoro must not be currently active."
        r = cls.getRedis()
        r.delete("pomodoro_active")
        r.delete("pomodoro_start_time")
        r.delete("pomodoro_end_time")
        r.delete("pomodoro_message")

        r.set("pomodoro_active", "1")
        r.set("pomodoro_start_time", cls.getTimeStr())

        return

    @classmethod
    def endActivePomodoro(cls):

        assert cls.pomodoroIsActive(), "Pomodoro must be active."
        r = cls.getRedis()
        msg = input("Pom message >> ")
        r.set("pomodoro_active", "0")
        r.set("pomodoro_end_time", cls.getTimeStr())

        r.set("pomodoro_message", msg)

        session = model.session()
        st_str = str(r.get("pomodoro_start_time"), 'utf-8')
        et_str = str(r.get("pomodoro_end_time"), 'utf-8')
        msg_str = str(r.get("pomodoro_message"), 'utf-8')
        activity_record = session.query(model.ActivityRecord).get(int(r.get("active_activityrecord_id")))
        pom = model.Pomodoro(start_time = isodate.parse_date(st_str),
                             end_time = isodate.parse_date(et_str),
                             message = msg_str,
                             activity_record = activity_record)
        session.add(pom)
        session.commit()

        # ActiveProject.addPomodoro(pom_id)

        return

    @classmethod
    def getStartTime(cls):
        r = cls.getRedis()
        time_str = str(r.get("pomodoro_start_time"), 'utf-8')
        return isodate.parse_datetime(time_str)

    @classmethod
    def getRuntime(cls):
        assert cls.pomodoroIsActive(), "Pomodoro must be active"
        start_time = cls.getStartTime()
        return int((datetime.datetime.utcnow() - start_time).total_seconds() / 60)

    @classmethod
    def pomodoroIsActive(cls):
        r = cls.getRedis()
        val = r.get("pomodoro_active")
        return val is not None and int(val)

class ActiveProject(RedisActiveRecord):
    @classmethod
    def showState(cls):
        r = cls.getRedis()
        print("active: {}".format(r.get("active")))
        print("active_start_time: {}".format(r.get("active_start_time")))
        print("active_end_time: {}".format(r.get("active_end_time")))
        print("active_activity_id: {}".format(r.get("active_activity_id")))
        print("active_pomodoro_list: {}".format(r.get("active_pomodoro_list")))
        print("active_activityrecord_id: {}".format(r.get("active_active_project_id")))
        return

    @classmethod
    def clearState(cls):
        r = cls.getRedis()
        r.delete("active")
        r.delete("active_start_time")
        r.delete("active_end_time")
        r.delete("active_activity_id")
        r.delete("active_pomodoro_list")
        r.delete("active_activityrecord_id")
        r.delete("active_activity_name")
        r.set("active", 0)
        return


    @classmethod
    def startActiveProject(cls, activity):
        assert not cls.projectIsActive(), "Project must not be currently active."
        r = cls.getRedis()
        r.delete("active")
        r.delete("active_start_time")
        r.delete("active_end_time")
        r.delete("active_activity_id")
        r.delete("active_pomodoro_list")
        r.delete("active_activityrecord_id")
        r.delete("active_activity_name")

        r.set("active", "1")
        start_time_str = cls.getTimeStr()
        r.set("active_start_time", start_time_str)
        r.set("active_activity_id", activity.id)
        r.set("active_activity_name", activity.name)

        session = model.session()
        activity_loc = session.query(model.Activity).get(activity.id)
        activityrecord = model.ActivityRecord(activity = activity_loc,
                                              start_time = isodate.parse_datetime(start_time_str))
        session.add(activityrecord)
        session.commit()
        r.set("active_activityrecord_id", activityrecord.id)
        return

    @classmethod
    def endActiveProject(cls):
        assert cls.projectIsActive(), "Project must be active."
        assert not ActivePomodoro.pomodoroIsActive(), "Must close all Pomodoros first."

        r = cls.getRedis()

        end_time_str = cls.getTimeStr()
        session = model.session()


        active_activityrecord_id = int(r.get("active_activityrecord_id"))
        act_rec = session.query(model.ActivityRecord).get(active_activityrecord_id)

        message = input("active project end summary >> ")

        act_rec.end_time = isodate.parse_datetime(end_time_str)
        act_rec.message = message
        session.add(act_rec)
        session.commit()

        cls.clearState()
        return

    @classmethod
    def projectIsActive(cls):
        r = cls.getRedis()
        val = r.get("active")
        return int(val)

    @classmethod
    def getCurrentActivityName(cls):
        assert cls.projectIsActive(), "Project must be active"
        r = cls.getRedis()
        activity_name = r.get("active_activity_name")
        return str(activity_name, 'utf-8')

    # @classmethod
    # def getCurrentActivity(cls, session):
    #     if not cls.projectIsActive(): return None
    #     r = cls.getRedis()
    #     active_activity_id = int(r.get("active_activity_id"))
    #     return session.query(model.Activity).get(active_activity_id)

    @classmethod
    def setActivity(cls, activity):
        activity_id = activity_id

    @classmethod
    def addPomodoro(cls, pomodoro):
        pom_id = pomodoro.id
        r = cls.getRedis()
        r.rpush("active_pomodoro_list", pom_id)
        return

    def clearActiveProject(self):
        return

class BreakStatus:
    def __init__(self):
        self.break_active = RedisVariable("break_active", int)
        self.break_start = RedisVariable("break_start", str)
        self.break_length = RedisVariable("break_length_min", int)
        self.break_end = RedisVariable("break_end", str)
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
            pdb.set_trace()
            break_string = self.break_end.value
            break_dt = self.parseDatetimeFromString(break_string)
            break_fin_string = self.getTimeStringFromVar(break_dt)
            return "Active: Ends at {}".format()

    on_break = property(lambda self : self.break_active.value)

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

class RedisVariable:
    def __init__(self, name, type = None):
        self.varname = name
        self.type = type if type is not None else False
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        return

    def getValue(self):
        value = self.r.get(self.varname)
        if value is None: return self.type()
        value_str = str(value, 'utf-8')
        if self.type:
            value = self.type(value_str)
        else:
            value = value_str
        return value

    def setValue(self, val):
        self.r.set(self.varname, val)
        return

    def __repr__(self):
        return str("xR{}".format(self.value))

    value = property(getValue, setValue)
