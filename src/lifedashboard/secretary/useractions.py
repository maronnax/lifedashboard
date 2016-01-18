from lifedashboard.status import WorkStatus
import datetime
import random
import lifedashboard.time
import time
from threading import Thread
import lifedashboard.model as model
import lifedashboard.tasks as tasks
import isodate
from IPython import embed
import os

import lifedashboard.tools as tools
import shutil
import pdb

def showDailySchedule(secretary):
    if secretary.current_schedule_file is None:
        print("No schedule has been established yet.  Why don't you create one?")
        return
    else:
        secretary.current_schedule.printSchedule(short = True)
    return

def createDailySchedule(secretary):
    def showScheduleList(schedule_files):
        for ndx, fn in enumerate(schedule_files):
            print("{}: {}".format(ndx+1, fn))
        return

    def showSchedule(fn):
        junk, base_name = os.path.split(fn)
        with open(fn) as schedule_file:
            for line in schedule_file.readlines():
                print(line, end="")
            else:
                print()
        return

    schedule_files = os.listdir(secretary.template_schedule_dir)
    showScheduleList(schedule_files)


    while True:
        userinput = input("Pick a schedule or select one to show> ").strip()
        if userinput.lower().startswith('s'):
            ndx = int(userinput[1:])
            showSchedule(os.path.join(secretary.template_schedule_dir, schedule_files[ndx-1]))
            continue
        elif userinput.lower().startswith('l'):
            showScheduleList(schedule_files)
            continue
        else:
            try:
                ndx = int(userinput)
                break
            except ValueError:
                print("Did not understand your input.")


    template_schedule_file = os.path.join(secretary.template_schedule_dir, schedule_files[ndx-1])
    print("Schedule is {}".format(template_schedule_file))
    outfile = secretary.getDailyScheduleFileName()

    shutil.copy(template_schedule_file, outfile)
    tools.editFileInteractively(outfile)
    secretary.registerDailyScheduleFile(outfile)
    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_WORK_ACTION

    return

def recordEmotionalState(secretary):
    curr_time = lifedashboard.time.getUTCTime()
    emotions = secretary.session.query(model.Emotion).order_by(model.Emotion.state.desc()).all()

    for ndx, emotion in enumerate(emotions):
        print("{}: {}".format(ndx+1, emotion))

    result = input("What are you feeling? ")
    results = map(int, result.split(","))
    current_emotions = [emotions[ndx-1] for ndx in results]

    description = input("How do you feel? ").strip()

    es = model.EmotionalState(time = curr_time, emotions = current_emotions, description = description)
    secretary.session.add(es)
    secretary.session.commit()
    return




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

    secretary.active_project.startActiveProject(activity, secretary)
    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_POMODORO_ACTION

    # Open the output file

    return

def endActiveProjectUserAction(secretary):
    print("Ending project")
    secretary.active_project.endActiveProject(secretary)

    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_WORK_ACTION
    return

def startActivePomodoroUserAction(secretary):
    session = secretary.session
    key_set = ["i am ready to work", "i will put my personal energy into the task at hand", "i am ready to focus"]
    key = random.choice(key_set)
    print("key: {}".format(key))

    # Get input
    while True:
        ret = input("type the key >> ").strip()
        if ret == key: break

    secretary.active_pomodoro.startActivePomodoro(secretary)
    activity_name = secretary.active_project.getCurrentActivityName()

    st = secretary.active_pomodoro.getStartTime()
    et = st + datetime.timedelta(seconds = 60 * 25)

    sts = st.strftime("%H%M")
    ets = et.strftime("%H%M")

    args = ["Pom: {}".format(activity_name),
            "{}-{}".format(sts,ets),
            "", secretary.active_pomodoro.pomodoro_uuid.value]

    args[2] = "Starting Pom. 25m left."
    tasks.say.delay(*args)

    args[2] = "2 minute drill.  Finish up."
    tasks.say.apply_async(args=args, countdown = 23 * 60)

    args[2] = "Pencils Down."
    tasks.interrupt.apply_async(args=args, countdown = 25 * 60)
    secretary.work_status.user_work_status = WorkStatus.POMODORO
    return

def endActivePomodoroUserAction(secretary):
    secretary.active_pomodoro.endActivePomodoro(secretary)
    secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_BREAK
    return

def showStatusUserAction(secretary):
    if secretary.work_status.user_work_status == WorkStatus.WAITING_FOR_SCHEDULE_ACTION:
        print("You are waiting to start your day.  Create a schedule.")
        return

    print(secretary.current_schedule.getCurrentEvent())

    if secretary.active_project.projectIsActive():
        print("You are working on the activity {}".format(secretary.active_project.getCurrentActivityName()))
    else:
        print("You are not currently working on any active projects.")
        return

    assert secretary.work_status.user_work_status != WorkStatus.WAITING_FOR_WORK_ACTION

    if secretary.active_pomodoro.pomodoroIsActive():
        minutes_left = 25 - secretary.active_pomodoro.getRuntime()
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds = minutes_left * 60)
        end_time_str = end_time.strftime("%H%M")
        print("There is an active pomodoro that will end in {} minutes at {}.".format(minutes_left, end_time_str))
        return

    assert secretary.work_status.user_work_status != WorkStatus.POMODORO

    if secretary.break_status.on_break:
        now = lifedashboard.time.getUTCTime()
        break_scheduled_end_time = isodate.parse_datetime(secretary.break_status.break_end.value)

        if break_scheduled_end_time < now:
            print("You are on break but should be done.  End it now")
        else:
            minutes_left = int((break_scheduled_end_time - now).total_seconds() / 60)
            print("You are on a break that ends in {0} minutes".format(minutes_left))

        return

    assert secretary.work_status.user_work_status != WorkStatus.BREAK


    if secretary.work_status.user_work_status == WorkStatus.WAITING_FOR_POMODORO_ACTION:
        print("Waiting to start a pomodoro.  Start one.")
        return

    assert secretary.work_status.user_work_status != WorkStatus.WAITING_FOR_POMODORO_ACTION

    if secretary.work_status.user_work_status == WorkStatus.WAITING_FOR_BREAK:
        print("Waiting to start your break.  Start it.")
        return

    assert secretary.work_status.user_work_status != WorkStatus.WAITING_FOR_BREAK
    assert 1 == 0, "Should never get here"
    return

def takeBreakUserAction(secretary, short_break = True):
    if secretary.active_pomodoro.pomodoroIsActive():
        print("There is an active pomodoro for {} more minutes")
        return
    else:
        if secretary.break_status.on_break:
            print("Already on break for {} more minutes.")
            return
        else:
            break_query = secretary.session.query(model.BreakActivity).order_by(model.BreakActivity.type.desc())
            if short_break:
                break_query = break_query.filter(model.BreakActivity.type == "short")
            else:
                break_query = break_query.filter(model.BreakActivity.type == "long")

            break_activities = break_query.all()
            for (ndx, ba) in enumerate(break_activities):
                print("{}: {}".format(ndx+1, ba))
            choice_ndx = int(input("Choice > ")) - 1

            secretary.break_status.startBreak(secretary, 5, break_query[choice_ndx])
            print("Starting 5 minute break.")
            args = ("Break ended", "", "Break is done.  Time to get back to work", secretary.break_status.break_uuid.value)
            # print("Running task with args={0}".format(args))
            tasks.yell.apply_async(args=args, countdown = 5 * 60)

            args = ("You should get back to work ASAP.", "", "Don't squander the day on breaks!  Find your focus and get back to it.", secretary.break_status.break_uuid.value)
            tasks.yell.apply_async(args=args, countdown = 7.5 * 60)

    # Start a thread that counts down the time

    def printCountdown(my_global, break_var):
        end_time = isodate.parse_datetime(break_var.break_end.value)
        while not my_global.quit:
            time.sleep(15)
            curr_time = lifedashboard.time.getUTCTime()
            time_left = (end_time - curr_time).total_seconds()

            if time_left > 0:
                min_left = int(time_left/60)
                sec_left = int(time_left - min_left*60)
                if not my_global.quit: print("{}:{:02d} left on break".format(min_left, sec_left))
            else:

                time_past = abs(time_left)
                min_past = int(time_past/60)
                sec_past = int(time_past - min_past*60)
                if not my_global.quit: print("You should be done with your break. It ended {}:{:02d} ago.".format(min_past, sec_past))

        return

    def quitThread(my_globals, thread):
        my_globals.quit = True
        thread.join()
        return

    thread_globals = secretary.Global()
    my_thread = Thread(target = printCountdown, args = (thread_globals, secretary.break_status))
    my_thread.start()
    secretary.work_status.user_work_status = WorkStatus.BREAK
    secretary.break_status.break_active.registerCallback(secretary.redis_callback_mgr, quitThread, 1, args=(thread_globals, my_thread))

    return

def endBreakUserAction(secretary):
    if not secretary.break_status.on_break:
        print("Not on break.")
        return
    else:
        print("Ending Break")
        secretary.break_status.endBreak(secretary)
        secretary.work_status.user_work_status = WorkStatus.WAITING_FOR_POMODORO_ACTION

        return
