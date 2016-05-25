#!/usr/bin/env python

import GoogleMaps
import RATP

lastError = ""

def getDist(mode, origins, destinations, timestamp = None, isArrivalTime = True,
    googleApiKey = None, useSuggestions = True, optimistic = 0, avoidTolls = False):
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
    global lastError
    if mode == MODE_TRANSIT:
        result = []
        for i in range(len(origins)):
            tmp = []
            for j in range(len(destinations)):
                current = RATP.getDistRATP(origins[i], destinations[j], timestamp,
                    isArrivalTime, useSuggestions)
                if current is None:
                    lastError = "RATP error: " + RATP.lastRATPError
                    return None
                tmp.append(current)
            result.append(tmp)
    else:
        result = GoogleMaps.getDistGoogle(mode, origins, destinations, timestamp,
            googleApiKey, optimistic, isArrivalTime, avoidTolls)
        if result is None:
            lastError = "GoogleMaps error: " + GoogleMaps.lastGoogleError
    return result

def getTimestamp(year, month, day, hour, minutes, seconds):
    return time.mktime((year, month, day, hour, minutes, seconds, -1, -1, -1))

if __name__ == "__main__":
    import sys
    def help():
        print("Usage: " + sys.argv[0] + " [arrive=time|depart=time] [gapikey=key] [nosuggest] [optimistic|pessimistic] [noTolls] originsFileName destinationsFileName")
        print("  where time can be a timestamp or of the form 'DD/MM/YYYY-HH:MM:SS'")
        sys.exit(0)
    # TODO

