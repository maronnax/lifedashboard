class Group:
    def displayStatus(self):
        raise Exception("Must overload.")

class FinancesGroup:
    def __init__(self):
        self.name = "Finances"
        return

    def displayStatus(self):
        print("Finance Status")
        return


class FitnessGroup:
    def __init__(self):
        self.name = "Fitness"
        return


    def displayStatus(self):
        print("Your Fitness Status is GOOD")
        return

class MeditationGroup:
    def __init__(self):
        self.name = "Meditation Practice"
        return


    def displayStatus(self):
        print("Meditation Status")
        return
