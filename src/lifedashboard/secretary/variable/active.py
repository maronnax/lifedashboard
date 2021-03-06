import isodate
from lifedashboard.redisvariable import RedisVariable
from lifedashboard.redisvariable import RedisList
import lifedashboard.model as model
import lifedashboard.time as time
import datetime
import uuid

class ActivePomodoro:
    pomodoro_active = RedisVariable("pomodoro_active", int)
    pomodoro_start_time = RedisVariable("pomodoro_start_time")
    pomodoro_end_time = RedisVariable("pomodoro_end_time")
    pomodoro_message = RedisVariable("pomodoro_message")
    pomodoro_uuid = RedisVariable("pomodoro_uuid")

    @classmethod
    def showState(cls):
        print("pomodoro_active: {}".format(cls.pomodoro_active.value))
        print("pomodoro_start_time: {}".format(cls.pomodoro_start_time.value))
        print("pomodoro_end_time: {}".format(cls.pomodoro_end_time.value))
        print("pomodoro_message: {}".format(cls.pomodoro_message.value))
        print("pomodoro_uuid: {}".format(cls.pomodoro_uuid.value))
        return

    @classmethod
    def clearState(cls):
        cls.pomodoro_active.clear()
        cls.pomodoro_start_time.clear()
        cls.pomodoro_end_time.clear()
        cls.pomodoro_message.clear()
        cls.pomodoro_active.clear()
        cls.pomodoro_uuid.clear()
        return

    @classmethod
    def startActivePomodoro(cls, secretary):
        assert ActiveProject.projectIsActive(), "Project must be active to start a pomodoro."
        assert not cls.pomodoroIsActive(), "Pomodoro must not be currently active."

        cls.pomodoro_active.clear()
        cls.pomodoro_start_time.clear()
        cls.pomodoro_end_time.clear()
        cls.pomodoro_message.clear()
        cls.pomodoro_uuid.clear()

        cls.pomodoro_active.value = 1
        cls.pomodoro_uuid.value = str(uuid.uuid4())
        cls.pomodoro_start_time.value = time.getUTCIsoformatTimeStr()
        return

    @classmethod
    def endActivePomodoro(cls, secretary, silent = False):
        assert cls.pomodoroIsActive(), "Pomodoro must be active."
        if not silent:
            msg = input("Pom message >> ")
        else:
            msg = ""
        cls.pomodoro_active.value = 0
        cls.pomodoro_end_time.value =  time.getUTCIsoformatTimeStr()
        cls.pomodoro_message.value = msg

        session = model.session()
        st_str = cls.pomodoro_start_time.value
        et_str = cls.pomodoro_end_time.value
        msg_str = cls.pomodoro_message.value

        activity_record = session.query(model.ActivityRecord).get(ActiveProject.project_activityrecord_id.value)
        pom = model.Pomodoro(start_time = isodate.parse_datetime(st_str),
                             end_time = isodate.parse_datetime(et_str),
                             message = msg_str,
                             activity_record = activity_record)
        session.add(pom)
        session.commit()

        start_time_str = time.formatTimeShort(time.convertUTCDTToLocal(pom.start_time))
        end_time_str = time.formatTimeShort(time.convertUTCDTToLocal(pom.end_time))
        extra_str = " - {0}".format(msg) if msg_str.strip() else ""
        line = "  Pomodoro: {0}-{1}{2}\n".format(start_time_str, end_time_str, extra_str)

        for fn in [activity_record.activity.getActivityEventRecordFilenameFromBaseDir(), secretary.getActivityRecordFilename()]:
            with open(fn, 'a') as out_file:
                out_file.write(line)
                out_file.flush()
        cls.clearState()
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
    project_active = RedisVariable("active", int)

    project_start_time = RedisVariable("project_start_time")
    project_end_time = RedisVariable("project_end_time")

    project_activity_name = RedisVariable("project_activity_name")
    project_activity_id = RedisVariable("project_activity_id")

    project_pomodoro_list = RedisList("project_pomodoro_list", int)

    project_activityrecord_id = RedisVariable("project_activityrecord_id")
    project_uuid = RedisVariable("project_uuid")

    @classmethod
    def getCurrentActivityName(cls):
        return cls.project_activity_name.value

    @classmethod
    def showState(cls):
        print("active: {}".format(cls.project_active.value))
        print("project_start_time: {}".format(cls.project_start_time.value))
        print("project_end_time: {}".format(cls.project_end_time.value))
        print("project_activity_name: {}".format(cls.project_activity_id.value))
        print("project_pomodoro_list: {}".format(cls.project_pomodoro_list.value))
        print("project_activityrecord_id: {}".format(cls.project_project_project_id.value))
        print("project_uuid: {}".format(cls.project_active_project_uuid.value))
        return

    @classmethod
    def clearState(cls):
        cls.project_active.clear()
        cls.project_start_time.clear()
        cls.project_end_time.clear()
        cls.project_pomodoro_list.clear()
        cls.project_activityrecord_id.clear()
        cls.project_activity_name.clear()
        cls.project_uuid.clear()
        cls.project_active.value = 0
        return

    @classmethod
    def startActiveProject(cls, activity, secretary):
        assert not cls.projectIsActive(), "Project must not be currently active."
        cls.project_active.clear()
        cls.project_start_time.clear()
        cls.project_end_time.clear()
        cls.project_pomodoro_list.clear()
        cls.project_activityrecord_id.clear()
        cls.project_activity_name.clear()
        cls.project_uuid.clear()

        cls.project_active.value = 1

        start_time = time.getUTCTime()
        start_time_str = start_time.isoformat()

        cls.project_uuid.value = str(uuid.uuid4())

        cls.project_start_time.value = start_time_str
        cls.project_activity_name.value = activity.name

        session = model.session()
        activity_loc = session.query(model.Activity).get(activity.id)
        activityrecord = model.ActivityRecord(activity = activity_loc,
                                              start_time = isodate.parse_datetime(start_time_str))
        session.add(activityrecord)
        session.commit()
        cls.project_activityrecord_id.value = activityrecord.id

        ##########

        # activity_record = secretary.session.query(model.ActiveProject).get(secretary.active_project.project_activityrecord_id)
        all_events_fn = secretary.getActivityRecordFilename()

        utc_start_time = start_time
        local_start_time = time.convertUTCDTToLocal(utc_start_time)
        local_start_time_str = time.formatTimeLong(local_start_time)
        line = "Activity {0} - Started {1}\n".format(activity.name, local_start_time_str)

        for fn in [activity.getActivityEventRecordFilenameFromBaseDir(), secretary.getActivityRecordFilename()]:
            with open(fn, 'a') as out_file:
                out_file.write(line)
                out_file.flush()
        return

    @classmethod
    def projectIsActive(cls):
        return bool(cls.project_active.value)

    @classmethod
    def endActiveProject(cls, secretary, silent = False):
        assert cls.projectIsActive(), "Project must be active."
        assert not ActivePomodoro.pomodoroIsActive(), "Must close all Pomodoros first."

        end_time = time.getUTCTime()
        end_time_str = end_time.isoformat()

        session = model.session()

        project_activityrecord_id = cls.project_activityrecord_id.value
        act_rec = session.query(model.ActivityRecord).get(project_activityrecord_id)
        if not silent:
            message = input("active project end summary >> ")
        else:
            message = ""

        # Write the code for linking the pomodoros to the active project.
        pomodoro_ids = cls.project_pomodoro_list.value
        act_rec.end_time = isodate.parse_datetime(end_time_str)
        act_rec.message = message

        session.add(act_rec)
        session.commit()

        utc_end_time = end_time
        local_end_time = time.convertUTCDTToLocal(utc_end_time)
        local_end_time_str = time.formatTimeLong(local_end_time)
        line = "Activity {0} - Ended {1}\n".format(act_rec.activity.name, local_end_time_str)

        for fn in [act_rec.activity.getActivityEventRecordFilenameFromBaseDir(), secretary.getActivityRecordFilename()]:
            with open(fn, 'a') as out_file:
                out_file.write(line)
                out_file.flush()

        cls.clearState()
        return
