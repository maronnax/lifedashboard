from lifedashboard.redisvariable import ActiveProject
from lifedashboard.redisvariable import ActivePomodoro
from lifedashboard.redisvariable import BreakStatus
import lifedashboard.model as model
import lifedashboard.tasks
import datetime

def setActiveProject(session):
    if ActiveProject.projectIsActive():
        lines = ["You are currently working on {}.".format(ActiveProject.getCurrentActivityName())]

        if ActivePomodoro.pomodoroIsActive():
            lines.append("There is {0} left to go in the current pomodoro.")

        print(" ".join(lines))
        if not input("Do you want to switch? ").lower().strip().startswith("y"):
            print("Ok.")
            return
        else:
            if ActivePomodoro.pomodoroIsActive():
                print("Ending pomodoro")
                ActivePomodoro.endActivePomodoro()

            ActiveProject.endActiveProject()

    focusgroups = session.query(model.FocusGroup).all()
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

    ActiveProject.startActiveProject(activity)

    return

def endActiveProject(session):
    print("Ending project")
    ActiveProject.endActiveProject()
    return

def startActivePomodoro(session):
    key = "i am ready to work"
    #key = ""
    print("key: {}".format(key))

    # Get input
    while True:
        ret = input("type the key >> ").strip()
        if ret == key: break

    ActivePomodoro.startActivePomodoro()

    activity_name = ActiveProject.getCurrentActivityName()

    st = ActivePomodoro.getStartTime()
    et = st + datetime.timedelta(seconds = 60 * 25)

    sts = st.strftime("%H%M")
    ets = et.strftime("%H%M")

    args = ["Pom: {}".format(activity_name),
            "{}-{}".format(sts,ets),
            ""]

    args[2] = "Starting Pom. 25m left."
    lifedashboard.tasks.say.delay(*args)

    args[2] = "2 minute drill.  Finish up."
    lifedashboard.tasks.say.apply_async(args=args, countdown = 23 * 60)

    args[2] = "Pencils Down."
    lifedashboard.tasks.interrupt.apply_async(args=args, countdown = 25 * 60)

    return

def endActivePomodoro(session):
    ActivePomodoro.endActivePomodoro()
    return


def showStatus(session):
    if ActiveProject.projectIsActive():
        print("You are working on {}".format(ActiveProject.getCurrentActivityName()))
    else:
        print("You are not currently working on any active projects.")
        return

    if ActivePomodoro.pomodoroIsActive():
        minutes_left = 25 - ActivePomodoro.getRuntime()
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds = minutes_left * 60)
        end_time_str = end_time.strftime("%H%M")
        print("There is an active pomodoro that will end in {} minutes at {}.".format(minutes_left, end_time_str))
    else:
        print("No pomodoros are running currently.")
    return

def showHelp(session):
    print("I know the following commands.")
    print("------------------------------------------")
    print("s             # Show current status")
    # print("ss            # Show daily status")
    #print("start day     # create your daily schedule.")
    print("start ap      # start active project")
    print("end ap        # End active project")
    print("start pom     # Start pomodoro")
    print("end pom       # End pomodoro")
    print("break         # Take a break.")
    print("end break         # End a break.")
    # print("a             # Away from computer")
    # print("b             # Away from computer")

    # print("res          # Record Emotional State")
    print("------------------------------------------")
    return

def showDailyStatus(session):
    print("Daily Status - IMPLEMENT")
    return




def takeBreak(session):
    if ActivePomodoro.pomodoroIsActive():
        print("There is an active pomodoro for {} more minutes")
        return
    else:
        bs = BreakStatus()
        if bs.on_break:
            print("Already on break for {} more minutes.")
            return
        else:

            possible_breaks = ["meditate and focus on you concentration",
                               "stretch", "do 20 pushups", "massage your arm",
                               "play a quick game of geometry wars", "read a poem",
                               "check facebook", "do some dishes"]

            bs.startBreak(5)
            print("Starting 5 minute break.")
            args = ("Break ended", "", "Break is done.  Time to get back to work")
            lifedashboard.tasks.say.apply_async(args=args, countdown = 5 * 60)
    return

def endBreak(session):
    bs = BreakStatus()
    if not bs.on_break:
        print("Not on break.")
        return
    else:
        print("Ending Break")
        bs.endBreak()
        return
