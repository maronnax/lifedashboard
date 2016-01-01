from lifedashboard.redisvariable import RedisVariable

class Status:
    pass

class UserPresenceStatus(Status):
    AWAY = 0
    AT_COMPUTER = 1

    _user_presence = RedisVariable("user_presence_status", int)

    def setUserPresence(self, var):
        self._user_presence.value = var

    user_presence = property(lambda self: self._user_presence.value, setUserPresence)

    @classmethod
    def advanceState(self):
        self.user_presence = 0 if self.user_presence == 1 else 1
        return

    def __repr__(self):
        if self.user_presence == 0:
            return "Away"
        elif self.user_presence == 1:
            return "Present"


class SecretaryStatus(Status):
    START_OF_DAY      = 0
    MONITOR_MORNING   = 1
    MONITOR_AFTERNOON = 2
    MONITOR_EVENING   = 3
    OFF_FOR_NIGHT     = 4

    def advanceState(self, next_state = None):
        self.secretary_status = (self.secretary_status+1)%5
        return

    def setSecretaryStatus(self, var):
        self._secretary_status.value = var

    _secretary_status = RedisVariable("secretary_status", int)
    secretary_status = property(lambda self: self._secretary_status.value, setSecretaryStatus)

    def __repr__(self):
        if self.secretary_status == self.START_OF_DAY:
            return "start of day"
        elif self.secretary_status == self.MONITOR_MORNING:
            return "monitor_morning"
        elif self.secretary_status == self.MONITOR_AFTERNOON:
            return "monitor_afternoon"
        elif self.secretary_status == self.MONITOR_EVENING:
            return "monitor_evening"
        elif self.secretary_status == self.OFF_FOR_NIGHT:
            return "off_for_night"

class WorkStatus(Status):
    WAITING_FOR_WORK_ACTION = 0
    POMODORO = 1
    WAITING_FOR_BREAK = 2
    BREAK = 3

    def setWorkStatus(self, var):
        self._user_work_status.value = var

    _user_work_status = RedisVariable("user_work_status", int)
    user_work_status = property(lambda self: self._user_work_status.value, setWorkStatus)

    # @classmethod
    def advanceState(self, next_state = None):
        self.user_work_status = (self.user_work_status + 1) % 4
        return

    def __repr__(self):
        if self.user_work_status == self.WAITING_FOR_WORK_ACTION:
            return "waiting_for_work_action"
        if self.user_work_status == self.POMODORO:
            return "pomodoro"
        if self.user_work_status == self.WAITING_FOR_BREAK:
            return "waiting_for_break"
        if self.user_work_status == self.BREAK:

            return "break"
