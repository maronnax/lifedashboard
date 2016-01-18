import time
import threading
import random
import pytz
import pickle
import datetime
import pytz
import subprocess
import copy
import os
import os
from IPython import embed
import speech_recognition
import nltk
import lifedashboard.model as model
import yaml
import redis
import isodate
import pdb

import lifedashboard.schedule
import lifedashboard.time
from lifedashboard.secretary.dbload import loadDatabaseData
from lifedashboard.secretary.dbload import getFocusDirectories
from lifedashboard.secretary.dbload import parseFocusDirectory
from lifedashboard.secretary.dbload import initializeFocusGroupFromFile
from lifedashboard.secretary.dbload import initializeActivityFromFile
from lifedashboard.secretary.dbload import loadEmotionalStatesFromFile
from lifedashboard.secretary.variable.dayactive import DayActive
from lifedashboard.secretary.variable.dayactive import DayLastReset

from lifedashboard.secretary.variable.active import ActiveProject
from lifedashboard.secretary.variable.active import ActivePomodoro
from lifedashboard.secretary.variable.breakstatus import BreakStatus

from lifedashboard.redisvariable import RedisVariable
from lifedashboard.redisvariable import RedisCallback

# from lifedashboard.secretary.useractions import setActiveProject
# from lifedashboard.secretary.useractions import endActiveProject
# from lifedashboard.secretary.useractions import startActivePomodoro
# from lifedashboard.secretary.useractions import endActivePomodoro
# from lifedashboard.secretary.useractions import showStatus
# from lifedashboard.secretary.useractions import takeBreak
# from lifedashboard.secretary.useractions import endBreak

from lifedashboard.status import WorkStatus

from lifedashboard.secretary.variable.active import ActiveProject
from lifedashboard.secretary.variable.active import ActivePomodoro
from lifedashboard.secretary.variable.breakstatus import BreakStatus
from lifedashboard.status import WorkStatus
import lifedashboard.model as model
# import lifedashboard.tasks
import datetime
import lifedashboard.secretary.useractions as useractions


def placeholderUserAction(secretary):
    print("Implement this action")
    return

class Secretary:
    active_project = ActiveProject()
    active_pomodoro = ActivePomodoro()
    break_status = BreakStatus()

    day_active = DayActive()
    day_last_reset = DayLastReset()

    class Global:
        def __init__(self):
            self.quit = False

    class SecretaryAction:
        def __init__(self, cmds, command_func, description, state_white_list = None, state_black_list = None):

            assert state_white_list is None or state_black_list is None, "Cannot set both a state_white_list and a state_black_list"

            self.description = description
            self.cmds = list(map(lambda s: s.strip(), cmds))
            self.command = command_func

            self.state_white_list = copy.copy(state_white_list)
            self.state_black_list = copy.copy(state_black_list)
            return

        def filter(self, state):
            if self.state_white_list is not None:
                return state.user_work_status in self.state_white_list

            if self.state_black_list is not None:
                return state.user_work_status not in self.state_black_list

            return True

        def commandStringMatches(self, cmd):
            return cmd.strip() in self.cmds

        def doUserAction(self):
            self.command()
            return


    def __init__(self, config):

        self.config = config
        self.database_directory = config.get("data_directory", is_filename = True)

        self.title_name = config.get("title_name")
        self.first_name = config.get("first_name")
        self.last_name = config.get("last_name")
        self.secretary_voice = config.get("secretary_voice", default="")
        self.secretary_rate = config.get("secretary_rate", default=0, type=int)
        self.timezone = pytz.timezone(config.get("timezone"))

        self.redis_callback_mgr = RedisCallback(poll_interval = 10)
        self.redis_callback_mgr.execute()

        loadDatabaseData(config)

        self.work_status = WorkStatus()

        self.work_status.addStartHook(WorkStatus.WAITING_FOR_SCHEDULE_ACTION, lambda : self.waitingForScheduleAction())
        self.work_status.addStartHook(WorkStatus.WAITING_FOR_WORK_ACTION, lambda : self.waitingForWorkSecretaryAction())
        self.work_status.addStartHook(WorkStatus.WAITING_FOR_POMODORO_ACTION, lambda : self.waitingForPomodoroSecretaryAction())
        self.work_status.addStartHook(WorkStatus.POMODORO, lambda: self.pomodoroSecretaryAction())
        self.work_status.addStartHook(WorkStatus.WAITING_FOR_BREAK, lambda: self.waitingForBreakSecretaryAction())
        self.work_status.addHook(WorkStatus.BREAK, lambda: self.breakSecretaryAction())

        self.template_schedule_dir = config.get("schedules_directory", "conf", is_filename = True)
        self.current_schedule_file = None
        self.current_schedule = None

        fn = self.getDailyScheduleFileName()
        if os.path.isfile(fn):
            self.current_schedule_file = fn
            self.current_schedule = lifedashboard.schedule.Schedule()
            self.current_schedule.parseFile(self.current_schedule_file)

        last_reset = self.day_last_reset.value
        if last_reset == "":
            self.day_active.value = 0
        else:
            current_time = lifedashboard.time.convertUTCDTToLocal(lifedashboard.time.getUTCTime())
            last_reset = lifedashboard.time.convertUTCDTToLocal(isodate.parse_datetime(self.last_reset))
            if current_time.day != last_reset.day:
                self.day_active.value = 0

        # self._initializeWorkStatus()

        self.actions = []

        # self.addUserAction(('ss',), : placeholderUserAction(self),                                  "Show daily status")
        self.addUserAction(('cds',),              lambda : useractions.createDailySchedule(self),           "Create your daily schedule", state_white_list = (WorkStatus.WAITING_FOR_SCHEDULE_ACTION, ))
        self.addUserAction(('sds',),              lambda : useractions.showDailySchedule(self),             "Show your daily schedule")
        self.addUserAction(('start ap',),         lambda : useractions.setActiveProjectUserAction(self),    "start active project", state_white_list = (WorkStatus.WAITING_FOR_WORK_ACTION, ))
        self.addUserAction(('end ap',),           lambda : useractions.endActiveProjectUserAction(self),    "end active project", state_black_list = (WorkStatus.POMODORO, WorkStatus.BREAK, WorkStatus.WAITING_FOR_WORK_ACTION, ))
        self.addUserAction(('start pom',),        lambda : useractions.startActivePomodoroUserAction(self), "start pomodoro", state_white_list = (WorkStatus.WAITING_FOR_POMODORO_ACTION, ))
        self.addUserAction(('end pom',),          lambda : useractions.endActivePomodoroUserAction(self),    "end pomodoro", state_white_list = (WorkStatus.POMODORO, ))
        self.addUserAction(('break',),            lambda : useractions.takeBreakUserAction(self),           "take a break", state_white_list=(WorkStatus.WAITING_FOR_BREAK, WorkStatus.WAITING_FOR_POMODORO_ACTION))
        self.addUserAction(('end break',),        lambda : useractions.endBreakUserAction(self),            "end break", state_white_list=(WorkStatus.BREAK, ))
        # self.addUserAction(('ac',),             lambda : placeholderUserAction(),                   "set away from computer")
        # self.addUserAction(('bc',),             lambda : placeholderUserAction(),                   "set back to computer")
        self.addUserAction(('res',),              lambda : useractions.recordEmotionalState(self),          "Record emotional state")
        self.addUserAction(('s', ),               lambda : useractions.showStatusUserAction(self),          "Show current status")
        self.addUserAction(('l',),                lambda : self.showHelpUserAction(), "Show help")
        self.addUserAction(('q',),                lambda : self.quitSessionUserAction(), "Quit the secretary")

        self.global_struct = self.Global()

        self.day_active.registerCallback(self.redis_callback_mgr, notifyOnDayStart)
        return

    def getActivityRecordFilename(self):
        return os.path.join(self.database_directory, "activityrecords", "events.txt")

    def getDailyScheduleFileName(self):
        tm = lifedashboard.time.convertUTCDTToLocal(lifedashboard.time.getUTCTime())
        schedule_filename = "schedule_{}.txt".format(tm.strftime("%b_%d_%Y"))
        return os.path.join(self.database_directory, "activityrecords", schedule_filename)

    def addUserAction(self, cmds, function, help_message, state_white_list = None, state_black_list = None):
        action = self.SecretaryAction(cmds, function, help_message, state_white_list, state_black_list)
        self.actions.append(action)
        return

    def quitSessionUserAction(self):
        self.global_struct.quit = True
        return

    def showHelpUserAction(self):
        print("I would userstand following commands can be executed now.")
        print("------------------------------------------")

        legal_actions = list(filter(lambda x: x.filter(self.work_status), self.actions))

        # LEGAL ACTIONS
        output_pairs  = []
        for action in legal_actions:
            output_pairs.append((",".join(action.cmds), action.description))

        lalign = max(map(len, map(lambda z: z[0], output_pairs))) + 5
        legal_lines = list(map(lambda z: "{0}# {1}".format(z[0].ljust(lalign), z[1]), output_pairs))

        for l in legal_lines:
            print(l)

        max_len = max(map(len, legal_lines))
        print("-" * int(max_len * 1.1))
        return

    ## DEFAULT ACTIONS

    def waitingForScheduleAction(self):
        print("You are just starting your day.  Please create your schedule")
        return

    def waitingForWorkSecretaryAction(self):
        print("There is no active project; you should start one.")
        return

    def waitingForPomodoroSecretaryAction(self):
        print("Start a pomodoro.")
        return

    def pomodoroSecretaryAction(self):
        activity_name = self.active_project.getCurrentActivityName()
        pom_remainder = 25 - self.active_pomodoro.getRuntime()
        print("You are currently working on a pomodoro for {} that ends in {} minutes".format(activity_name, pom_remainder))
        return

    def waitingForBreakSecretaryAction(self):
        print("Time to take a break! Start it ASAP.")
        return

    def breakSecretaryAction(self):
        print("You are currently taking a break.")
        return

    ###

    def _initializeWorkStatus(self):
        project_is_active = self.active_project.projectIsActive()
        pomodoro_is_active = self.active_pomodoro.pomodoroIsActive()
        break_is_active = self.break_status.on_break

        if self.current_schedule is None:
            if pomodoro_is_active:
                self.active_pomodoro.endActivePomodoro(self, silent = True)
            if break_is_active:
                self.break_status.endBreak()
            if project_is_active:
                self.active_project.endActiveProject(self, silent = True)
            self.work_status.user_work_status = WorkStatus.WAITING_FOR_SCHEDULE_ACTION

        elif pomodoro_is_active:
            self.work_status.user_work_status = WorkStatus.POMODORO
        elif break_is_active:
            self.work_status.user_work_status = WorkStatus.BREAK
        elif project_is_active:
            # Could also be WorkStatus.WAITING_FOR_BREAK
            self.work_status.user_work_status = WorkStatus.WAITING_FOR_POMODORO_ACTION
        else:
            self.work_status.user_work_status = WorkStatus.WAITING_FOR_WORK_ACTION

        return


    def run(self):
        # This initializes anything that should happen in the current
        # state.
        self._initializeWorkStatus()
        # self.work_status.updateWorkStatus(self.work_status.user_work_status)

        try:
            thread = threading.Thread(target = self.secretarySpeak, args = (self.global_struct, ))
            thread.start()

            self.secretaryInput(self.global_struct)
        except KeyboardInterrupt:
            print("Got keyboard interrupt.")
            self.global_struct.quit = True
        thread.join()
        self.redis_callback_mgr.quit()

        return

    def secretaryInput(self, global_struct):
        # Start an active project
        # Start a pomodoro if none is active
        # End a running pomodoro
        # End an active Project.

        self.session = model.session()
        while not global_struct.quit:

            user_input = input("").strip().lower()

            try:
                self.executeUserInput(global_struct, user_input)

            except AssertionError as xcpt:
                print(xcpt)

        self.session.commit()
        self.session.flush()
        self.session.close()
        return


    def executeUserInput(self, global_struct, user_input):
        legal_actions = list(filter(lambda x: x.filter(self.work_status), self.actions))
        matching_cmds = list(filter(lambda act: act.commandStringMatches(user_input), legal_actions))

        if len(list(matching_cmds)) == 0:
            print("Unrecognized input - {}".format(user_input))

        for action in matching_cmds:
            action.doUserAction()

        return

    def secretarySpeak(self, global_struct):
        last_branch = -1

        while not global_struct.quit:
            time.sleep(1)
            # If there is an inactive project, alert
            # If there is an active project but no pomodoro, alert
            # If there is a pomodoro that should be finished, alert

            # if not ActiveProject.projectIsActive():
            #     branch_id = 1
            #     if not last_branch == branch_id:
            #     last_branch = branch_id

            # if ActiveProject.projectIsActive() and not ActivePomodoro.pomodoroIsActive():
            #     branch_id = 2
            #     activity_name = ActiveProject.getCurrentActivityName()
            #     if not last_branch == branch_id: print("There is no active pomodoro for activity {} . Start one.".format(activity_name))
            #     last_branch = branch_id

            # if ActivePomodoro.pomodoroIsActive():
            #     if ActivePomodoro.getRuntime() >= 25:
            #         branch_id = 3
            #         if not last_branch == branch_id: print("Pomodoro is done.  Please end it and start your break.")
            #         last_branch = branch_id
            #     else:
            #         branch_id = 4
            #         if not last_branch == branch_id:

            #             last_branch = branch_id
        return

    def registerDailyScheduleFile(self, schedule_fn):
        # load the file and create alerts
        self.current_schedule_file = schedule_fn
        self.current_schedule = lifedashboard.schedule.Schedule()
        self.current_schedule.parseFile(self.current_schedule_file)
        return

###

def notifyOnDayStart():
    print("Your day has started.  Get to the computer.")
    return
