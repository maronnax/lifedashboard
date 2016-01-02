import lifedashboard.tasks as tasks
from lifedashboard.status import WorkStatus
import datetime
import lifedashboard.model as model

def setActiveProjectUserAction(secretary):
    assert secretary.work_status.user_work_status == WorkStatus.WAITING_FOR_WORK_ACTION, "Cannot set active project unless existing ap's, pomodoros, and breaks are closed"

    focusgroups = secretary.session.query(model.FocusGroup).all()
    print("What would you like to work on?")
    for (ndx, focus) in enumerate(focusgroups):
        print("{}: {}".format(ndx+1,focus))
    ndx = int(input("Choice? ")) - 1

    activelifegroup = focusgroups[ndx]
    print("What would you like to work on?")
    group_activities = activelifegroup.activities
    for (ndx, potential_activity) in enumerate(group_activities):
        print("{}: {} - expect it will take {}".format(ndx+1, potential_activity.name, potential_activity.expected_time))
    ndx = int(input("Choice? ")) - 1
    activity = group_activities[ndx]

    secretary.active_project.startActiveProject(activity)
    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_POMODORO_ACTION
    return

def endActiveProjectUserAction(secretary):
    print("Ending project")
    secretary.active_project.endActiveProject()

    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_WORK_ACTION
    return

def startActivePomodoroUserAction(secretary):
    session = secretary.session
    key = "i am ready to work"
    #key = ""
    print("key: {}".format(key))

    # Get input
    while True:
        ret = input("type the key >> ").strip()
        if ret == key: break

    secretary.active_pomodoro.startActivePomodoro()
    activity_name = secretary.active_project.getCurrentActivityName()

    st = secretary.active_pomodoro.getStartTime()
    et = st + datetime.timedelta(seconds = 60 * 25)

    sts = st.strftime("%H%M")
    ets = et.strftime("%H%M")

    args = ["Pom: {}".format(activity_name),
            "{}-{}".format(sts,ets),
            ""]

    args[2] = "Starting Pom. 25m left."
    tasks.say.delay(*args)

    args[2] = "2 minute drill.  Finish up."
    tasks.say.apply_async(args=args, countdown = 23 * 60)

    args[2] = "Pencils Down."
    tasks.interrupt.apply_async(args=args, countdown = 25 * 60)
    secretary.work_status.user_work_status = WorkStatus.POMODORO
    return

def endActivePomodoroUserAction(secretary):
    secretary.active_pomodoro.endActivePomodoro()
    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_BREAK
    return

def showStatusUserAction(secretary):
    if secretary.active_project.projectIsActive():
        print("You are working on {}".format(secretary.active_project.getCurrentActivityName()))
    else:
        print("You are not currently working on any active projects.")
        return

    if secretary.active_pomodoro.pomodoroIsActive():
        minutes_left = 25 - secretary.active_pomodoro.getRuntime()
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds = minutes_left * 60)
        end_time_str = end_time.strftime("%H%M")
        print("There is an active pomodoro that will end in {} minutes at {}.".format(minutes_left, end_time_str))
    else:
        print("No pomodoros are running currently.")
    return


def takeBreakUserAction(secretary):
    if secretary.active_pomodoro.pomodoroIsActive():
        print("There is an active pomodoro for {} more minutes")
        return
    else:
        if secretary.break_status.on_break:
            print("Already on break for {} more minutes.")
            return
        else:

            possible_breaks = ["meditate and focus on you concentration",
                               "stretch", "do 20 pushups", "massage your arm",
                               "play a quick game of geometry wars", "read a poem",
                               "check facebook", "do some dishes"]

            secretary.break_status.startBreak(5)
            print("Starting 5 minute break.")
            args = ("Break ended", "", "Break is done.  Time to get back to work")
            tasks.say.apply_async(args=args, countdown = 5 * 60)

    secretary.work_status.user_work_status = WorkStatus.BREAK
    return

def endBreakUserAction(secretary):
    if not secretary.break_status.on_break:
        print("Not on break.")
        return
    else:
        print("Ending Break")
        secretary.break_status.endBreak()

        secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_POMODORO_ACTION
        return
