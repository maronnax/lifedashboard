import isodate
from lifedashboard.redisvariable import RedisVariable
from lifedashboard.redisvariable import RedisList
import lifedashboard.model as model
import lifedashboard.time as time
import datetime

class ActivePomodoro:
    pomodoro_active = RedisVariable("pomodoro_active", int)
    pomodoro_start_time = RedisVariable("pomodoro_start_time")
    pomodoro_end_time = RedisVariable("pomodoro_end_time")
    pomodoro_message = RedisVariable("pomodoro_message")

    @classmethod
    def showState(cls):
        print("pomodoro_active: {}".format(cls.pomodoro_active.value))
        print("pomodoro_start_time: {}".format(cls.pomodoro_start_time.value))
        print("pomodoro_end_time: {}".format(cls.pomodoro_end_time.value))
        print("pomodoro_message: {}".format(cls.pomodoro_message))
        return

    @classmethod
    def clearState(cls):
        cls.pomodoro_active.clear()
        cls.pomodoro_start_time.clear()
        cls.pomodoro_end_time.clear()
        cls.pomodoro_message.clear()
        cls.pomodoro_active.clear()
        return

    @classmethod
    def startActivePomodoro(cls):
        assert ActiveProject.projectIsActive(), "Project must be active to start a pomodoro."
        assert not cls.pomodoroIsActive(), "Pomodoro must not be currently active."

        cls.pomodoro_active.clear()
        cls.pomodoro_start_time.clear()
        cls.pomodoro_end_time.clear()
        cls.pomodoro_message.clear()

        cls.pomodoro_active.value = 1
        cls.pomodoro_start_time.value = time.getUTCIsoformatTimeStr()
        return

    @classmethod
    def endActivePomodoro(cls):
        assert cls.pomodoroIsActive(), "Pomodoro must be active."
        msg = input("Pom message >> ")
        cls.pomodoro_active.value = 0
        cls.pomodoro_end_time.value =  time.getUTCIsoformatTimeStr()
        cls.pomodoro_message.value = msg

        session = model.session()
        st_str = cls.pomodoro_start_time.value
        et_str = cls.pomodoro_end_time.value
        msg_str = cls.pomodoro_message.value

        activity_record = session.query(model.ActivityRecord).get(ActiveProject.active_activityrecord_id.value)
        pom = model.Pomodoro(start_time = isodate.parse_date(st_str),
                             end_time = isodate.parse_date(et_str),
                             message = msg_str,
                             activity_record = activity_record)
        session.add(pom)
        session.commit()

        return

    @classmethod
    def getStartTime(cls):
        return isodate.parse_datetime(cls.pomodoro_start_time.value)

    @classmethod
    def getRuntime(cls):
        assert cls.pomodoroIsActive(), "Pomodoro must be active"
        start_time = cls.getStartTime()
        return int((datetime.datetime.utcnow() - start_time).total_seconds() / 60)

    @classmethod
    def pomodoroIsActive(cls):
        val = cls.pomodoro_active.value
        return bool(val)

class ActiveProject:
    active = RedisVariable("active", int)

    active_start_time = RedisVariable("active_start_time")
    active_end_time = RedisVariable("active_end_time")
    active_activity_name = RedisVariable("active_activity_name")
    active_activity_id = RedisVariable("active_activity_id")

    active_pomodoro_list = RedisList("active_pomodoro_list", int)
    active_activityrecord_id = RedisVariable("active_activityrecord_id")

    @classmethod
    def getCurrentActivityName(cls):
        return cls.active_activity_name.value

    @classmethod
    def showState(cls):
        print("active: {}".format(active.value))
        print("active_start_time: {}".format(active_start_time.value))
        print("active_end_time: {}".format(active_end_time.value))
        print("active_activity_name: {}".format(active_activity_id.value))
        print("active_pomodoro_list: {}".format(active_pomodoro_list.value))
        print("active_activityrecord_id: {}".format(active_active_project_id.value))
        return

    @classmethod
    def clearState(cls):
        cls.active.clear()
        cls.active_start_time.clear()
        cls.active_end_time.clear()
        cls.active_pomodoro_list.clear()
        cls.active_activityrecord_id.clear()
        cls.active_activity_name.clear()
        cls.active.value = 0
        return


    @classmethod
    def startActiveProject(cls, activity):
        assert not cls.projectIsActive(), "Project must not be currently active."
        cls.active.clear()
        cls.active_start_time.clear()
        cls.active_end_time.clear()
        cls.active_pomodoro_list.clear()
        cls.active_activityrecord_id.clear()
        cls.active_activity_name.clear()

        cls.active.value = 1

        start_time = time.getUTCTime()
        start_time_str = start_time.isoformat()

        cls.active_start_time.value = start_time_str
        cls.active_activity_name.value = activity.name

        session = model.session()
        activity_loc = session.query(model.Activity).get(activity.id)
        activityrecord = model.ActivityRecord(activity = activity_loc,
                                              start_time = isodate.parse_datetime(start_time_str))
        session.add(activityrecord)
        session.commit()
        cls.active_activityrecord_id.value = activityrecord.id
        return

    @classmethod
    def projectIsActive(cls):
        return bool(cls.active.value)

    @classmethod
    def endActiveProject(cls):
        assert cls.projectIsActive(), "Project must be active."
        assert not ActivePomodoro.pomodoroIsActive(), "Must close all Pomodoros first."

        end_time = time.getUTCTime()
        end_time_str = end_time.isoformat()

        session = model.session()

        active_activityrecord_id = cls.active_activityrecord_id.value
        act_rec = session.query(model.ActivityRecord).get(active_activityrecord_id)
        message = input("active project end summary >> ")

        # Write the code for linking the pomodoros to the active project.
        pomodoro_ids = cls.active_pomodoro_list.value
        act_rec.end_time = isodate.parse_datetime(end_time_str)
        act_rec.message = message

        session.add(act_rec)
        session.commit()

        cls.clearState()
        return
