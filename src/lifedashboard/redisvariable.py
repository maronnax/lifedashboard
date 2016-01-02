import redis
import isodate
import datetime
import lifedashboard.model as model # BLECK!
import pdb


class RedisVariable:
    def __init__(self, name, type = str):
        self.varname = name
        self.type = type if type is not None else False
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
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
