#!/usr/bin/env python

import modes
import GoogleMaps
import RATP
import time
import re
import sys

lastError = ""
unrecognizedAddresses = []

def getDist(mode, origins, destinations, timestamp = None, isArrivalTime = True,
    googleApiKey = None, useSuggestions = True, optimistic = 0, avoidTolls = False, dispProgress = False):
    """
    Returns a table of time (seconds) results for each couple of origin / destination,
    or None if an error happened (then read lastError).
    mode: Transportation mode (see defs.py)
    origins: List of origins
    destinations: List of destinations
    timestamp: The arrival (or departure) timestamp
    isArrivalTime: Set it to False to indicate that timestamp is the departure time
    googleApiKey: The Google API key that is required to make certain requests
    useSuggestions: Do we want to accept address corrections, and automatically choose the first suggestion?
    optimistic: 0 for best guess, -1 for pessimistic and 1 for optimistic (driving conditions)
    avoidTolls: Parameter set for the driving mode
    """
    global lastError, unrecognizedAddresses
    if mode == modes.MODE_TRANSIT:
        result = []
        dp = 0
        if dispProgress:
            sys.stdout.write(str(dp) + "%\r")
            sys.stdout.flush()
        for i in range(len(origins)):
            tmp = []
            for j in range(len(destinations)):
                if dispProgress:
                    cp = int(100.0 * (i + float(j) / len(destinations)) / len(origins))
                    if cp > dp:
                        dp = cp
                        sys.stdout.write(str(dp) + "%\r")
                        sys.stdout.flush()
                current = RATP.getDistRATP(origins[i], destinations[j], timestamp,
                    isArrivalTime, useSuggestions)
                if current is None:
                    lastError = "RATP error: " + RATP.lastRATPError
                    return None
                tmp.append(current)
            result.append(tmp)
        if dispProgress:
            sys.stdout.write("100%\n")
            sys.stdout.flush()
        unrecognizedAddresses += RATP.RATPToChange
        RATP.RATPToChange = []
    else:
        GOOGLE_LIMIT_GLOBAL = 100
        GOOGLE_LIMIT_PERLIST = 25
        stepD = min(GOOGLE_LIMIT_GLOBAL, len(destinations), GOOGLE_LIMIT_PERLIST)
        stepO = min(max(1, int(GOOGLE_LIMIT_GLOBAL / len(destinations))), GOOGLE_LIMIT_PERLIST)
        i1 = 0
        result = []
        dp = 0
        if dispProgress:
            sys.stdout.write(str(dp) + "%\r")
            sys.stdout.flush()
        while i1 < len(origins):
            mO = min(stepO, len(origins) - i1)
            subOrigins = origins[i1:i1 + mO]
            subR = [[] for i2 in range(mO)]
            j1  = 0
            while j1 < len(destinations):
                if dispProgress:
                    cp = int(100.0 * (i1 + float(j1) / len(destinations)) / len(origins))
                    if cp > dp:
                        dp = cp
                        sys.stdout.write(str(dp) + "%\r")
                        sys.stdout.flush()
                mD = min(stepD, len(destinations) - j1)
                subDestinations = destinations[j1:j1 + mD]
                subresult = GoogleMaps.getDistGoogle(mode, subOrigins, subDestinations, timestamp,
                    googleApiKey, optimistic, isArrivalTime, avoidTolls)
                if subresult is None:
                    lastError = "GoogleMaps error: " + GoogleMaps.lastGoogleError
                    return None
                for i2 in range(mO):
                    subR[i2] += subresult[i2]
                j1 += stepD
            result += subR
            i1 += stepO
        if dispProgress:
            sys.stdout.write("100%\n")
            sys.stdout.flush()
        unrecognizedAddresses += GoogleMaps.GoogleNotFound
        GoogleMaps.GoogleNotFound = []
    return result

def getTimestamp(year, month, day, hour, minutes, seconds):
    return int(time.mktime((year, month, day, hour, minutes, seconds, -1, -1, -1)))

getTimestampFromStr_RE = re.compile("^(\\d{2})/(\\d{2})/(\\d{4})-(\\d{2}):(\\d{2}):(\\d{2})$")

def getTimestampFromStr(s):
    match = getTimestampFromStr_RE.match(s)
    if match:
        return getTimestamp(int(match.group(3)), int(match.group(2)), int(match.group(1)), int(match.group(4)), int(match.group(5)), int(match.group(6)))
    try:
        return int(s)
    except ValueError:
        print("Warning: unrecognized date '" + s + "'; set to now instead.")
        return int(time.time())

if __name__ == "__main__":
    import sys
    def help():
        print("Usage: " + sys.argv[0] + " [mode=walk|bicycle|car|transit] [arrive=time|depart=time] [gapikey=key] " +
            "[nosuggest] [optimistic|pessimistic] [noTolls] originsFileName destinationsFileName outputFileName")
        print("  where time can be a timestamp or of the form 'DD/MM/YYYY-HH:MM:SS'")
        sys.exit(0)
    if len(sys.argv) < 4:
        help()
    mode = modes.MODE_CAR
    timestamp = None
    isArrivalTime = True
    googleApiKey = None
    useSuggestions = True
    optimistic = 0
    avoidTolls = False
    for i in range(1, len(sys.argv) - 3):
        if sys.argv[i] == "mode=walk":
            mode = modes.MODE_WALK
        elif sys.argv[i] == "mode=bicycle":
            mode = modes.MODE_BICYCLE
        elif sys.argv[i] == "mode=car":
            mode = modes.MODE_CAR
        elif sys.argv[i] == "mode=transit":
            mode = modes.MODE_TRANSIT
        elif sys.argv[i][:7] == "arrive=":
            timestamp = getTimestampFromStr(sys.argv[i][7:])
            isArrivalTime = True
        elif sys.argv[i][:7] == "depart=":
            timestamp = getTimestampFromStr(sys.argv[i][7:])
            isArrivalTime = False
        elif sys.argv[i][:8] == "gapikey=":
            googleApiKey = sys.argv[i][8:]
        elif sys.argv[i] == "nosuggest":
            useSuggestions = False
        elif sys.argv[i] == "optimistic":
            optimistic = 1
        elif sys.argv[i] == "pessimistic":
            optimistic = -1
        elif sys.argv[i] == "noTolls":
            avoidTolls = True
        else:
            print("Unrecognized argument: '" + sys.argv[i] + "'")
            help()
    with open(sys.argv[-3], 'r') as f1:
        f1lines = f1.readlines()
    f1lines = map(lambda x: x.strip(), f1lines)
    f1lines = filter(lambda x: x != "", f1lines)
    with open(sys.argv[-2], 'r') as f2:
        f2lines = f2.readlines()
    f2lines = map(lambda x: x.strip(), f2lines)
    f2lines = filter(lambda x: x != "", f2lines)
    result = getDist(mode, f1lines, f2lines, timestamp, isArrivalTime,
        googleApiKey, useSuggestions, optimistic, avoidTolls)
    if len(unrecognizedAddresses):
        print("Unrecognized:")
        def disp(x):
            print("  " + x)
        map(disp, unrecognizedAddresses)
    if result is None:
        print("Error; last error message:")
        print(lastError)
        sys.exit(0)
    with open(sys.argv[-1], 'w') as f:
        for row in result:
            f.write('\t'.join(map(str, row)) + "\n")
    print("Done.")

