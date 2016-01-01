"""Main dashboard app"""
from lifedashboard.groups import FinancesGroup
from lifedashboard.groups import FitnessGroup
from lifedashboard.groups import MeditationGroup

class Dashboard(object):
    def __init__(self):
        "Init method for the Dashboard application"

        self.dashboard_groups = [FinancesGroup(), FinancesGroup(), MeditationGroup()]
        return

    def runIteration(self):
        # self.printStatus()

        for ndx,item in enumerate(self.dashboard_groups):
            print("{0}: {1}".format(ndx+1, item.name))

        return False



    def run(self):
        while True:
            res = self.runIteration()
            if not res: break

    # def printStatus(self):
    #     for grp in self.dashboard_groups:
    #         grp.displayStatus()
    #     return
