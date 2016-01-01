import time
import threading
import random
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
import lifedashboard.tasks
import yaml
import redis
import isodate
import pdb

from lifedashboard.secretary.dbload import loadDatabaseData
from lifedashboard.secretary.dbload import getFocusDirectories
from lifedashboard.secretary.dbload import parseFocusDirectory
from lifedashboard.secretary.dbload import initializeFocusGroupFromFile
from lifedashboard.secretary.dbload import initializeActivityFromFile
from lifedashboard.secretary.dbload import loadEmotionalStatesFromFile

from lifedashboard.redisvariable import ActiveProject
from lifedashboard.redisvariable import ActivePomodoro
from lifedashboard.redisvariable import BreakStatus

from lifedashboard.secretary.actions import setActiveProject
from lifedashboard.secretary.actions import endActiveProject
from lifedashboard.secretary.actions import startActivePomodoro
from lifedashboard.secretary.actions import endActivePomodoro
from lifedashboard.secretary.actions import showStatus
from lifedashboard.secretary.actions import showHelp
from lifedashboard.secretary.actions import showDailyStatus
from lifedashboard.secretary.actions import takeBreak
from lifedashboard.secretary.actions import endBreak

class Secretary:

    class Global:
        def __init__(self):
            self.quit = False


    def __init__(self, config):
        self.config = config

        self.title_name = config.get("title_name")
        self.first_name = config.get("first_name")
        self.last_name = config.get("last_name")
        self.secretary_voice = config.get("secretary_voice", default="")
        self.secretary_rate = config.get("secretary_rate", default=0, type=int)
        self.timezone = pytz.timezone(config.get("timezone"))

        loadDatabaseData(config)

        return

    def run(self):
        try:
            global_struct = self.Global()
            thread = threading.Thread(target = self.secretarySpeak, args = (global_struct, ))
            thread.start()

            self.secretaryInput(global_struct)
        except KeyboardInterrupt:
            print("Got keyboard interrupt.")
            global_struct.quit = True
        thread.join()
        return

    def secretaryInput(self, global_struct):
        # Start an active project
        # Start a pomodoro if none is active
        # End a running pomodoro
        # End an active Project.

        session = model.session()
        while not global_struct.quit:
            user_input = input("").strip().lower()
            if user_input in ['quit', 'q']:
                global_struct.quit = True
                continue
            elif user_input in ["list", "l"]:
                showHelp(session)
            elif user_input == 's':
                showStatus(session)
            elif user_input == 'ss':
                showDailyStatus(session)
            elif user_input == 'start ap':
                setActiveProject(session)
            elif user_input == 'start pom':
                startActivePomodoro(session)
            elif user_input == 'end pom':
                endActivePomodoro(session)
            elif user_input == 'end ap':
                endActiveProject(session)
            elif user_input == 'break':
                takeBreak(session)
            elif user_input == 'end break':
                endBreak(session)
            else:
                print("Unrecognized input - {}".format(user_input))

        session.commit()
        session.flush()
        session.close()
        return

    def secretarySpeak(self, global_struct):
        last_branch = -1

        while not global_struct.quit:
            time.sleep(1)
            # If there is an inactive project, alert
            # If there is an active project but no pomodoro, alert
            # If there is a pomodoro that should be finished, alert

            if not ActiveProject.projectIsActive():
                branch_id = 1
                if not last_branch == branch_id: print("There is no active project; you should start one.")
                last_branch = branch_id

            if ActiveProject.projectIsActive() and not ActivePomodoro.pomodoroIsActive():
                branch_id = 2
                activity_name = ActiveProject.getCurrentActivityName()
                if not last_branch == branch_id: print("There is no active pomodoro for activity {} . Start one.".format(activity_name))
                last_branch = branch_id

            if ActivePomodoro.pomodoroIsActive():
                if ActivePomodoro.getRuntime() >= 25:
                    branch_id = 3
                    if not last_branch == branch_id: print("Pomodoro is done.  Please end it and start your break.")
                    last_branch = branch_id
                else:
                    branch_id = 4
                    if not last_branch == branch_id:
                        activity_name = ActiveProject.getCurrentActivityName()
                        pom_remainder = 25 - ActivePomodoro.getRuntime()
                        print("You are currently working on a pomodoro for {} that ends in {} minutes".format(activity_name, pom_remainder))
                        last_branch = branch_id
        return



###
