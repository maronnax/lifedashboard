import redis
import isodate
import datetime
import lifedashboard.model as model # BLECK!
from threading import Thread
import time
import pdb

class RedisCallback:
    def __init__(self, poll_interval):
        self.variable_getvalue = {}
        self.variable_curvalue = {}
        self.variable_callbacks = {}
        self.variable_repeat_callback = {}
        self.variable_arguments = {}

        self.run_poll = True
        self.thread = None
        self.poll_interval = poll_interval

        return

    def quit(self):
        self.run_poll = False
        if self.thread is not None:
            self.thread.join()
        return

    def execute(self):
        self.thread = Thread(target = self.pollCallbacks)
        self.thread.start()
        return

    def addCallback(self, variable, callback, fire_times = -1, args = ()):
        variable_name = variable.varname
        getValue = lambda : variable.value

        self.variable_getvalue[variable_name] = getValue
        self.variable_curvalue[variable_name] = getValue()
        self.variable_callbacks[variable_name] = callback
        self.variable_repeat_callback[variable_name] = fire_times
        self.variable_arguments[variable_name] = args
        return

    def pollCallbacks(self):
        while self.run_poll:
            items = list(self.variable_curvalue.items()) # B/c things can remove themselves during run
            for (var_name, var_cur_value) in items:
                new_value = self.variable_getvalue[var_name]()

                if var_cur_value != new_value:
                    # print("Firing {}".format(var_name))
                    self.variable_curvalue[var_name] = new_value
                    self.variable_callbacks[var_name](*self.variable_arguments[var_name])
                    self.variable_repeat_callback[var_name] -= 1
                    if not self.variable_repeat_callback[var_name]:
                        self.variable_curvalue.pop(var_name)
                        self.variable_callbacks.pop(var_name)
                        self.variable_repeat_callback.pop(var_name)
                        self.variable_getvalue.pop(var_name)
                        self.variable_arguments.pop(var_name)
            time.sleep(self.poll_interval)
        return

class RedisVariable:
    def __init__(self, name, type = str):
        self.varname = name
        self.type = type if type is not None else False
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        return

    def registerCallback(self, callback_manager, cb, fire_times = -1, args = ()):
        callback_manager.addCallback(self, cb, fire_times, args)
        return

    def getValue(self):
        value = self.r.get(self.varname)
        if value is None: return self.type()
        value_str = str(value, 'utf-8')
        if self.type:
            value = self.type(value_str)
        else:
            value = value_str
        return value

    def setValue(self, val):
        self.r.set(self.varname, val)
        return

    def clear(self):
        self.r.delete(self.varname)
        return

    value = property(getValue, setValue)

    def __repr__(self):
        return str("xR{}".format(self.value))

class RedisList:
    def __init__(self, name, type = str):
        self.varname = name
        self.type = type if type is not None else False
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.callbacks = []
        return

    def registerCallback(self, callback_mgr, cb):
        callback_mgr.addCallback(self, cb)
        return

    def rpush(self, value):
        self.r.rpush(self.varname, value)
        return

    def rpop(self):
        ret_val = self.r.rpop(self.varname)
        if ret_val is not None:
            ret_val = str(ret_val, 'utf-8')
        else:
            ret_val = self.type()
        return self.type(ret_val)


    def lpush(self, value):
        self.r.lpush(self.varname, value)
        return

    def lpop(self):
        ret_val = self.r.lpop(self.varname)
        if ret_val is not None:
            ret_val = str(ret_val, 'utf-8')
        else:
            ret_val = self.type()
        return self.type(ret_val)

    def mapByteStringToValue(self, value):
        if value is None: return self.type()

        value = str(value, 'utf-8')
        return self.type(value)

    def lrange(self, start_ndx, end_ndx):
        ret_array = self.r.lrange(self.varname, start_ndx, end_ndx)
        ret_array = map(lambda val: self.mapByteStringToValue(val), ret_array)
        return list(ret_array)

    def getValue(self):
        return self.lrange(0, -1)

    def setValue(self, value):
        self.clear()

        for v in value:
            self.rpush(v)
        return

    value = property(getValue, setValue)

    def _getValueFromString(self, value):
        if value is None: return self.type()
        value_str = str(value, 'utf-8')
        if self.type:
            value = self.type(value_str)
        else:
            value = value_str
        return value

    def clear(self):
        self.r.delete(self.varname)
        return

    def __repr__(self):
        return str("xR{}".format(self.value))
