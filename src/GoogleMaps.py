import requests
import time
from defs import *

lastGoogleError = ""

def getDistGoogle(mode, origins, destinations, timestamp = None,
    apiKey = None, optimistic = 0, isArrivalTime = True, avoidTolls = False):
    """
    Returns a table of time (seconds) results for each couple of origin / destination,
    or None if an error happened (then read lastGoogleError).
    mode: Transportation mode (see defs.py)
    origins: List of origins (addresses or GPS coordinates, e.g. "41.43206,-81.38992")
    destinations: List of destinations (addresses or GPS coordinates)
    timestamp: The arrival (or departure) timestamp
    apiKey: The Google API key that is required to make certain requests
    optimistic: 0 for best guess, -1 for pessimistic and 1 for optimistic (driving conditions)
    isArrivalTime: Set it to False to indicate that timestamp is the departure time
    avoidTolls: Parameter set for the driving mode
    """
    global lastGoogleError, MODE_WALK, MODE_BICYCLE, MODE_CAR, MODE_TRANSIT
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    url += "?origins=" + '|'.join(origins)
    url += "&destinations=" + '|'.join(destinations)
    url += "&mode=" + {MODE_WALK: "walking", MODE_BICYCLE: "bicycling",
        MODE_CAR: "driving", MODE_TRANSIT: "transit"}.get(mode, "driving")
    if avoidTolls and (mode == MODE_CAR):
        url += "&avoid=tolls"
    if timestamp is None:
        timestamp = int(time.time()) + 1
    if isArrivalTime:
        url += "&arrival_time=" + str(timestamp)
    else:
        url += "&departure_time=" + str(timestamp)
    if (optimistic < 0) and (mode == MODE_CAR):
        url += "&traffic_model=pessimistic"
    elif (optimistic > 0) and (mode == MODE_CAR):
        url += "&traffic_model=optimistic"
    if apiKey is not None:
        url += "&key=" + apiKey
    r = requests.get(url)
    if r.status_code != 200:
        lastGoogleError = "Status code: " + str(r.status_code)
        return None
    json = r.json()
    if json["status"] != "OK":
        lastGoogleError = "Status: " + json["status"]
        return None
    result = []
    for i in range(len(json["rows"])):
        row = json["rows"][i]
        tmp = []
        for j in range(len(row["elements"])):
            el = row["elements"][j]
            if el["status"] != "OK":
                lastGoogleError = ("SubStatus: " + el["status"] + " on origin '" +
                    origins[i] + "' / destination '" + destination[j] + "'")
                return None
            tmp.append(int(el["duration"]["value"]))
        result.append(tmp)
    return result

