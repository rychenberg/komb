# -------------------------------------------------------------------------------------------------------------------- #
# Project           : Daten-Kombinierer
# Program name      : komb
# Author            : mk
# Date created      : Feb 2022
# Purpose           : Class to hold and process Data-Columns
#
# Revision History  :
# Date      Author   Rev    Revision
# 5.2.22    mk       0      Initialversion
# 25.2.22   mk       1      Some Improvements...
# -------------------------------------------------------------------------------------------------------------------- #
from datetime import datetime

class TimeSeries:
    def __init__(self, name):
        self.name = name.replace("\n", "")
        self.timestamp = []
        self.timestring = []
        self.data = []

    def add_value(self, timestamp, value, timestring=""):
        value = value.replace(",", ".")

        try:
            float_value = float(value)
        except:
            return

        self.timestamp.append(timestamp)
        self.timestring.append(timestring)
        self.data.append(float_value)

    def print_stat(self):
        timeformat = "%d.%m.%y %H:%M:%S"

        if len(self.data) < 1 or len(self.timestamp) < 1:
            # Datenreihe ist leer
            return [self.name,
                    len(self.data),
                    "-",
                    "-"]

        starttime = self.first_timestamp()
        endtime   = self.last_timestamp()

        return [self.name,
                len(self.data),
                datetime.fromtimestamp(starttime).strftime(timeformat),
                datetime.fromtimestamp(endtime).strftime(timeformat)]

    def first_timestamp(self):
        if len(self.data) < 1 or len(self.timestamp) < 1:
            # Datenreihe ist leer
            return float('nan')

        return min([ts.timestamp() for ts in self.timestamp])

    def last_timestamp(self):
        if len(self.data) < 1 or len(self.timestamp) < 1:
            # Datenreihe ist leer
            return float('nan')

        return max([ts.timestamp() for ts in self.timestamp])

    def get_value_str(self, timestamp, number_format, decimal_separator):

        if timestamp < self.first_timestamp() or timestamp > self.last_timestamp():
            return ""

        for i, ts in enumerate(self.timestamp):
            if ts.timestamp() > timestamp:
                return ("{" + number_format + "}").format(self.data[i-1]).replace(".", decimal_separator)

        return ""
