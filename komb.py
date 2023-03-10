#!/usr/bin/python3

# -------------------------------------------------------------------------------------------------------------------- #
# Project           : Daten-Kombinierer
# Program name      : komb
# Author            : mk
# Date created      : Feb 2022
# Purpose           : Help to make datafiles usable! (and learn Python)
#
# Revision History  :
# Date      Author   Rev    Revision
# 5.2.22    mk       0      Initialversion
# 25.2.22   mk       1      Some Improvements...
# 29.9.22   mk       2      Weitere Verbesserungen, besonders eine enorme Geschwindigkeitserhöhung.
# -------------------------------------------------------------------------------------------------------------------- #
import math
import sys
import configparser
import csv
import cProfile
from datetime import datetime
from timeseries import TimeSeries

def load_timeseries(data_file, cfg_file):
    if "RawDataStructure" not in cfg_file:
        print("Sektion \"RawDataStructure\" fehlt in Config-File.")
        return -1, []

    encoding = cfg_file["RawData"]["Encoding"]
    if encoding == "utf-8":
        encoding = "utf-8-sig"  #Zusatz "-sig" entfernt das Byte Order Mark (BOM) vom Dateianfang

    delimiter = cfg_file["RawDataStructure"]["Delimiter"]

    # Gesamtes Datenfile einlesen
    with open(data_file, mode='r', encoding=encoding) as csvfile:
        datareader = csv.reader(csvfile, delimiter=delimiter)
        rawdata = [row for row in datareader]

    # Titelzeile der Datenreihen extrahieren
    try:
        col_id_row = int(cfg_file["RawDataStructure"]["ColumnIdentifierRow"])-1
    except KeyError as err:
        print(print(f"Fehler im Config-File: {err=}, {type(err)=}"))
        return -1, []

    col_id = rawdata[col_id_row]

    #print("Titel", col_id)
    #for row in rawdata[int(cfg_file["RawDataStructure"]["ColumnIdentifierLine"]):]:
    #    print("Daten:", row)

    # Plausibilisierung: Haben alle Datenzeilen gleich viele Spalten wie die Titelzeile?
    if any([len(row)!=len(col_id) for row in rawdata]):
        print("Nicht alle Zeilen gleich lang")
        return -1, []

    try:
        timestamp_col = int(cfg_file["RawDataStructure"]["TimestampColumn"])-1
    except KeyError as err:
        print(print(f"Fehler im Config-File: {err=}, {type(err)=}"))
        return -1, []


    # Plausibilisierung: Gibt es rechts neben dem Zeitstempel auch noch Daten-Spalten?
    res=len(col_id) - (timestamp_col + 1)
    if len(col_id) - (timestamp_col + 1) < 1:
        print("Keine Daten-Spalten rechts vom Zeitstempel")
        return -1, []

    try:
        timestamp_format = cfg_file["RawDataStructure"]["TimestampFormat"].strip()
    except KeyError as err:
        print(print(f"Fehler im Config-File: {err=}, {type(err)=}"))
        return -1, []


    # Timeseries Objekte erzeugen
    ts = [TimeSeries(col) for col in col_id[timestamp_col+1:]]

    # TimeSeries Objekte mit Werten befüllen
    for row in rawdata[col_id_row+1:]:
        dt = datetime.strptime(row[timestamp_col], timestamp_format).timestamp()
        #print(row)

        for i, col in enumerate(row[timestamp_col+1:]):
            ts[i].add_value(dt, col, row[timestamp_col])

    return 1, ts

def print_stats(ts_data):
    stat = []
    for ts in ts_data:
        stat.append(ts.print_stat())

    col_width = max([len(s[0]) for s in stat])
    format_string = "{:<" + str(col_width) + "}  {:>6}  {:<17}  {:<17}"
    print(format_string.format("Name", "Anzahl", "Von...", "Bis..."))
    for s in stat:
        print(format_string.format(*s))

def print_progress(last, progress):
    current = math.floor(progress*10)/10

    if current > last:
        print("\r" + str(int(current*100)) + "%", end="")

    return current

def main():
    program_version = "22.9-dev_2"

    # Programm Parameter prüfen
    if len(sys.argv) < 2:
        print("Bitte Config-File angeben.")
        sys.exit()

    # Konfiguration lesen
    cfg_file_name = sys.argv[1]
    cfg_file = configparser.ConfigParser(interpolation=None)
    cfg_file.read(cfg_file_name, encoding="utf-8")
    try:
        data_files = cfg_file["RawData"]["DataFiles"].split(",")
        data_files = [x.strip() for x in data_files]
    except KeyError as err:
        print("Keine Datenfiles unter RawData/DataFiles angegeben.")
        return

    # Daten lesen
    ts_data = []
    for file in data_files:
        print("Bearbeite", file)
        status, ts = load_timeseries(file, cfg_file)
        if status == 1:
            ts_data = ts_data + ts

    # Statistik der gelesenen Daten ausgeben
    print_stats(ts_data)

    # Daten ausgeben
    output_file = cfg_file["OutputFileStructure"]["OutputFile"]
    delimiter   = cfg_file["OutputFileStructure"]["Delimiter"]
    timeformat  = cfg_file["OutputFileStructure"]["TimestampFormat"]
    interval    = int(cfg_file["OutputFileStructure"]["Interval"])
    number_format = cfg_file["OutputFileStructure"]["NumberFormat"]
    decimal_separator = cfg_file["OutputFileStructure"]["DecimalSeparator"]

    print("Exportiere...")
    progress = -1
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        datawriter = csv.writer(csvfile, dialect="excel", delimiter=delimiter)

        #Spaltenüberschriften schreiben
        datawriter.writerow(["Timestamp"]+[ts.name for ts in ts_data])

        first_timestamp = min([ts.first_timestamp() for ts in ts_data])
        first_timestamp = math.floor(first_timestamp/interval)*interval
        print("Von", datetime.fromtimestamp(first_timestamp).strftime(timeformat))

        last_timestamp = max([ts.last_timestamp() for ts in ts_data])
        last_timestamp = math.floor(last_timestamp / interval) * interval
        print("Bis", datetime.fromtimestamp(last_timestamp).strftime(timeformat))

        for timestamp in range(first_timestamp, last_timestamp+1, interval): # last_timestamp+1 damit range den letzten Zeitstempel mit nimmt
            #print(datetime.fromtimestamp(timestamp).strftime(timeformat))
            datawriter.writerow([datetime.fromtimestamp(timestamp).strftime(timeformat)]+[ts.get_value_str(timestamp, number_format, decimal_separator) for ts in ts_data])
            progress = print_progress(progress, (timestamp-first_timestamp)/(last_timestamp-first_timestamp))

if __name__ == "__main__":
    #cProfile.run('main()')
    main()

