import lifedashboard.time
import pytz
import datetime
import pdb

class Schedule:
    def __init__(self):

        self.name = None
        self.daily_event = []
        return

    def parseFile(self, schedule_fn):
        with open(schedule_fn) as schedule_file:
            schedule = list(map(lambda line: line.strip(), list(schedule_file.readlines())))

            marker_indicate = list(map(self.linesIsMarker, schedule))
            if True in marker_indicate:
                marker_index = marker_indicate.index(True)
                self.name = schedule[0]
                schedule = schedule[marker_index+1:]

            for line in schedule:
                components = line.split()
                time_str = components[0]

                times = list(map(self.parseTime, time_str.split("-")))
                description = " ".join(components[1:])

                self.daily_event.append( (times, description))
        return

    def writeFile(self, fn):
        return

    def timeLeftInCurrentEvent(self):
        ndx = self.getCurrentEventNdx()

        if ndx == len(self.daily_event) - 1:
            return -1

        current_time = lifedashboard.time.getUTCTime()
        return self.daily_event[ndx+1][0][0] - current_time

    def getCurrentEventNdx(self):
        curr_time = lifedashboard.time.getUTCTime()
        for ndx in range(len(self.daily_event)):
            if len(self.daily_event[ndx][0]) == 1: continue
            if self.daily_event[ndx][0][0] <= curr_time and curr_time < self.daily_event[ndx][0][1]:
                return ndx
        else:
            return ndx

    def getCurrentEvent(self):
        ndx = self.getCurrentEventNdx()
        return self._createLineFromScheduleEntry(ndx)

    def printSchedule(self, short = False):
        lines = []

        if self.name is not None and not short:
            lines.append(self.name)
            lines.append("-" * 25)

        current_ndx = self.getCurrentEventNdx()

        for ndx in range(len(self.daily_event)):
            line = self._createLineFromScheduleEntry(ndx)

            if current_ndx == ndx:
                lines.append("-> {}".format(line))
            else:
                lines.append("   {}".format(line))
        for l in lines:
            print(l)
        return

    def _createLineFromScheduleEntry(self, ndx):

        entry = self.daily_event[ndx]
        (time_array, description) = entry
        assert 1 <= len(time_array) <= 2
        if len(time_array) == 1:
            time_str = lifedashboard.time.formatTimeShort(lifedashboard.time.convertUTCDTToLocal(time_array[0]))
        elif len(time_array) == 2:
            time_str = "{}-{}".format(lifedashboard.time.formatTimeShort(lifedashboard.time.convertUTCDTToLocal(time_array[0])),
                                      lifedashboard.time.formatTimeShort(lifedashboard.time.convertUTCDTToLocal(time_array[1])))

        return "{} {}".format(time_str, description)

    @staticmethod
    def linesIsMarker(line):
        if len(set(line)) == 1 and "-" in line:
            return True
        else:
            return False

    @staticmethod
    def parseTime(time_str):
        hour_str = time_str[:2]
        minute_str = time_str[2:]
        hour = int(hour_str)
        minute = int(minute_str)
        local_time = lifedashboard.time.convertUTCDTToLocal(lifedashboard.time.getUTCTime())

        try:

            if hour == 0 and minute == 0:
                parsed_time = (local_time + datetime.timedelta(days=1)).replace(hour = hour, minute = 0)
            else:
                parsed_time = local_time.replace(hour = hour, minute = minute)
            local_time = parsed_time.replace(second = 0, microsecond = 0)
            utc_time = local_time.astimezone(pytz.utc)
        except ValueError as xcpt:
            print("--> Cannot understand time to parse, got {}.  Tried to parse '{}':'{}'".format(time_str,hour_str,minute_str))
            raise xcpt

        return utc_time.replace(tzinfo=None)


    @staticmethod
    def parseTimeLine(time_str):
        if "-" in time_str:
            time_str_array = list(map(lambda x: x.strip(), time_str.split("-")))
        else:
            time_str_array = [time_str]

        times = list(map(parseTime, time_str_array))
        return
