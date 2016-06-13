#!/usr/bin/env python

import PyDist
import os.path
import modes
import re
import time
from datetime import datetime, timedelta

reDayDate = re.compile("^([A-Z][a-z]+)-(\\d{2}):(\\d{2}):(\\d{2})$")
days = {"Monday":0, "Tuesday":1, "Wednesday":2, "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6}

if __name__ == "__main__":
    import sys
    answer = raw_input("Mode? (walk|bicycle|car|transit) [transit]: ")
    if answer == "walk":
        mode = modes.MODE_WALK
    elif answer == "bicycle":
        mode = modes.MODE_BICYCLE
    elif answer == "car":
        mode = modes.MODE_CAR
    elif (answer == "transit") or (answer == ""):
        mode = modes.MODE_TRANSIT
    else:
        print("Error: Unrecognized answer.")
        sys.exit(0)
    useRATP = True
    if mode == modes.MODE_TRANSIT:
        answer = raw_input("Use RATP? (y/n) [y]: ")
        if answer == "n":
            useRATP = False
        elif (answer == "y") or (answer == ""):
            useRATP = True
        else:
            print("Error: Unrecognized answer.")
            sys.exit(0)
    answer = raw_input("Do you want to set the arrive time instead of the departure time? (y/n) [n]: ")
    if answer == "y":
        isArrivalTime = True
    elif (answer == "n") or (answer == ""):
        isArrivalTime = False
    else:
        print("Error: Unrecognized answer.")
        sys.exit(0)
    answer = raw_input("Time? (timestamp, DD/MM/YYYY-HH:MM:SS or DayOfWeek-HH:MM:SS) [Monday-08:30:00]: ")
    timestamp = None
    try:
        timestamp = int(answer)
    except ValueError:
        if (len(answer) == 19) and (answer[2] == '/'):
            timestamp = PyDist.getTimestampFromStr(answer)
        else:
            if answer == "":
                answer = "Monday-08:30:00"
            matchObj = reDayDate.match(answer)
            if not matchObj:
                print("Error: wrong answer format.")
                sys.exit(0)
            if not matchObj.group(1) in days:
                print("Error: Wrong day ('" + matchObj.group(1) + "')")
                sys.exit(0)
            oday = days[matchObj.group(1)]
            ohour = int(matchObj.group(2))
            ominute = int(matchObj.group(3))
            osecond = int(matchObj.group(4))
            ts = time.time()
            now = datetime.fromtimestamp(ts)
            ts += 60 - now.second
            ts += 60 * (59 - now.minute)
            ts += 3600 * (23 - now.hour)
            ts += 86400 * ((6 + oday - now.weekday()) % 7)
            ts += 3600 * ohour + 60 * ominute + osecond
            timestamp = int(ts)
            print("Datetime used: " + str(datetime.fromtimestamp(timestamp)))
    gkeyFilename = raw_input("Google API key filename? [google.key]: ")
    if gkeyFilename == "":
        gkeyFilename = "google.key"
    if os.path.isfile(gkeyFilename):
        with open(gkeyFilename, 'r') as f:
            googleApiKey = f.readlines()[0].strip()
    else:
        print("Error: The file '" + gkeyFilename + "' does not exist.")
        sys.exit(0)
    answer = raw_input("Use the first RATP suggestion (y/n) [y]: ")
    if answer == "n":
        useSuggestions = False
    elif (answer == "y") or (answer == ""):
        useSuggestions = True
    else:
        print("Error: Unrecognized answer.")
        sys.exit(0)
    answer = raw_input("Use optimistic (1), pessimistic (-1) or best guess (0) duration evaluation? [0]: ")
    if answer == "1":
        optimistic = 1
    elif answer == "-1":
        optimistic = -1
    elif (answer == "0") or (answer == ""):
        optimistic = 0
    else:
        print("Error: Unrecognized answer.")
        sys.exit(0)
    answer = raw_input("Avoid tolls? (y/n) [n]: ")
    if answer == "y":
        avoidTolls = True
    elif (answer == "n") or (answer == ""):
        avoidTolls = False
    else:
        print("Error: Unrecognized answer.")
        sys.exit(0)
    originsFilename = raw_input("Origins filename? [origins.txt]: ")
    if originsFilename == "":
        originsFilename = "origins.txt"
    if not os.path.isfile(originsFilename):
        print("Error: The file '" + originsFilename + "' does not exist.")
        sys.exit(0)
    destinationsFilename = raw_input("Destinations filename? [destinations.txt]: ")
    if destinationsFilename == "":
        destinationsFilename = "destinations.txt"
    if not os.path.isfile(destinationsFilename):
        print("Error: The file '" + destinationsFilename + "' does not exist.")
        sys.exit(0)
    outputFilename = raw_input("Output filename? [durations.txt]: ")
    if outputFilename == "":
        outputFilename = "durations.txt"
    print("Computing...")
    result = None
    try:
        with open(originsFilename, 'r') as f1:
            f1lines = f1.readlines()
        f1lines = map(lambda x: x.strip(), f1lines)
        f1lines = filter(lambda x: x != "", f1lines)
        with open(destinationsFilename, 'r') as f2:
            f2lines = f2.readlines()
        f2lines = map(lambda x: x.strip(), f2lines)
        f2lines = filter(lambda x: x != "", f2lines)
        result = PyDist.getDist(mode, f1lines, f2lines, timestamp, isArrivalTime,
            googleApiKey, useSuggestions, optimistic, avoidTolls, useRATP, True)
    except:
        print("Unexpected error:", sys.exc_info()[1])
    if len(PyDist.unrecognizedAddresses):
        print("Unrecognized:")
        def disp(x):
            print("  " + x)
        map(disp, PyDist.unrecognizedAddresses)
    if result is None:
        print("Error; last error message:")
        print(PyDist.lastError)
        raw_input("Press Enter to exit")
        sys.exit(0)
    with open(outputFilename, 'w') as f:
        for row in result:
            f.write('\t'.join(map(str, row)) + "\n")
    print("Done.")
    raw_input("Press Enter to exit")

