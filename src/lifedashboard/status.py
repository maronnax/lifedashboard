from lifedashboard.redisvariable import RedisVariable
import collections

class WorkStatus:
    WAITING_FOR_WORK_ACTION = 0
    WAITING_FOR_POMODORO_ACTION = 1
    POMODORO = 2
    WAITING_FOR_BREAK = 3
    BREAK = 4

    begin_hooks = collections.defaultdict(lambda : [])
    hooks = collections.defaultdict(lambda : [])
    end_hooks = collections.defaultdict(lambda :[])

    def execHooks(self, state):

        for h in self.begin_hooks[state]:
            h()

        for h in self.hooks[state]:
            h()

        for h in self.end_hooks[state]:
            h()

        return

    def addHook(self, status, func):
        self.hooks[status].append(func)

    def addStartHook(self, status, func):
        self.begin_hooks[status].append(func)

    def addEndHook(self, status, func):
        self.end_hooks[status].append(func)

    def resetWorkStatus(self, var):
        self._user_work_status.value = var

    def updateWorkStatus(self, var):
        self._user_work_status.value = var
        self.execHooks(var)

    _user_work_status = RedisVariable("user_work_status", int)
    user_work_status = property(lambda self: self._user_work_status.value, updateWorkStatus)

    def __repr__(self):
        if self.user_work_status == self.WAITING_FOR_WORK_ACTION:
            return "waiting_for_work_action"
        if self.user_work_status == self.POMODORO:
            return "pomodoro"
        if self.user_work_status == self.WAITING_FOR_BREAK:
            return "waiting_for_break"
        if self.user_work_status == self.BREAK:
            return "break"
