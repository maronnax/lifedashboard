from lifedashboard.redisvariable import RedisVariable
def DayActive():
    return RedisVariable("day_active", int)

def DayLastReset():
    return RedisVariable("day_last_reset")
