import requests
import time
import modes
import urllib

lastGoogleError = ""
GoogleNotFound = []

def getDistGoogle(mode, origins, destinations, timestamp = None,
    apiKey = None, optimistic = 0, isArrivalTime = True, avoidTolls = False):
    """
    Returns a table of time (seconds) results for each couple of origin / destination,
    or None or with -1s inside if an error happened (then read lastGoogleError).
    mode: Transportation mode (see defs.py)
    origins: List of origins (addresses or GPS coordinates, e.g. "41.43206,-81.38992")
    destinations: List of destinations (addresses or GPS coordinates)
    timestamp: The arrival (or departure) timestamp
    apiKey: The Google API key that is required to make certain requests
    optimistic: 0 for best guess, -1 for pessimistic and 1 for optimistic (driving conditions)
    isArrivalTime: Set it to False to indicate that timestamp is the departure time
    avoidTolls: Parameter set for the driving mode
    """
    global lastGoogleError, GoogleNotFound
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    url += "?origins=" + urllib.quote('|'.join(origins), '|')
    url += "&destinations=" + urllib.quote('|'.join(destinations), '|')
    url += "&mode=" + {modes.MODE_WALK: "walking", modes.MODE_BICYCLE: "bicycling",
        modes.MODE_CAR: "driving", modes.MODE_TRANSIT: "transit"}.get(mode, "driving")
    if avoidTolls and (mode == modes.MODE_CAR):
        url += "&avoid=tolls"
    if timestamp is None:
        timestamp = int(time.time()) + 1
    if isArrivalTime:
        url += "&arrival_time=" + str(timestamp)
    else:
        url += "&departure_time=" + str(timestamp)
    if (optimistic < 0) and (mode == modes.MODE_CAR):
        url += "&traffic_model=pessimistic"
    elif (optimistic > 0) and (mode == modes.MODE_CAR):
        url += "&traffic_model=optimistic"
    if apiKey is not None:
        url += "&key=" + apiKey
    r = requests.get(url)
    if r.status_code != 200:
        lastGoogleError = "Status code: " + str(r.status_code) + " on URL: '" + url + "'"
        return None
    json = r.json()
    if json["status"] != "OK":
        lastGoogleError = "Status: " + json["status"] + " on URL: '" + url + "'"
        return None
    result = []
    origs = json["origin_addresses"]
    for i in range(len(origs)):
        if origs[i] == "":
            GoogleNotFound.append("Google: origin " + origins[i].decode("utf8"))
    dests = json["destination_addresses"]
    for j in range(len(dests)):
        if dests[j] == "":
            GoogleNotFound.append("Google: destination " + destinations[j].decode("utf8"))
    for i in range(len(json["rows"])):
        if origs[i] == "":
            continue
        row = json["rows"][i]
        tmp = []
        for j in range(len(row["elements"])):
            if dests[j] == "":
                continue
            el = row["elements"][j]
            if el["status"] == "NOT_FOUND":
                GoogleNotFound.append("Google: " + origins[i].decode("utf8") + " to " + destinations[j].decode("utf8"))
                tmp.append(-1)
            elif el["status"] == "ZERO_RESULTS":
                tmp.append(-1)
            elif el["status"] != "OK":
                lastGoogleError = ("SubStatus: " + el["status"] + " on origin '" +
                    origins[i].decode("utf8") + "' / destination '" + destinations[j].decode("utf8") + "'")
                return None
            else:
                if "duration_in_traffic" in el:
                    tmp.append(int(el["duration_in_traffic"]["value"]))
                else:
                    tmp.append(int(el["duration"]["value"]))
        result.append(tmp)
    return result

