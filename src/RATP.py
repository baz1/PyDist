import requests
import time
import re
import string

lastRATPError = ""

reRATPTime = re.compile("<dt class=\"mask\">Horaires</dt>\\s*<dd class=\"time\">\\s*" +
    "<b>((?:(?!</b>).)*)</b>")
reRATPSafeStr = re.compile("^\\d+(?:h\\d*)?$")
reRATPOption = re.compile("<option value=\"([^\"]+)\">")
reRATPPrintable = set(string.printable)

def getDistRATP(origin, destination, timestamp = None, isArrivalTime = True, useSuggestions = True):
    """
    Returns the number of seconds for the itinerary
    or None if an error happened (then read lastRATPError).
    origin: Address of origin
    destination: Address of destination
    timestamp: The arrival (or departure) timestamp
    isArrivalTime: Set it to False to indicate that timestamp is the departure time
    useSuggestions: Do we want to accept address corrections, and automatically choose the first suggestion?
    """
    global lastRATPError, reRATPTime, reRATPSafeStr, reRATPOption, reRATPPrintable
    url = "http://www.ratp.fr/itineraires/fr/ratp/recherche-avancee"
    url += "?start=" + origin;
    url += "&end=" + destination;
    if isArrivalTime:
        url += "&is_date_start=-1"
    else:
        url += "&is_date_start=1"
    if timestamp is None:
        timestamp = int(time.time()) + 1
    mtime = time.localtime(timestamp)
    def twoDigits(sn):
        res = str(sn)
        if len(res) < 2:
            return "0" + res
        return res
    url += ("&date=" + twoDigits(mtime.tm_mday) + "%2F" + twoDigits(mtime.tm_mon) +
        "%2F" + str(mtime.tm_year))
    url += "&time[hour]=" + str(mtime.tm_hour)
    url += "&time[minute]=" + str(mtime.tm_min)
    url += "&mode=all&route_type=1&avoid="
    r = requests.get(url)
    if r.status_code != 200:
        lastRATPError = "Status code: " + str(r.status_code)
        return None
    mtext = r.text.encode('utf-8')
    def myIndexOf(haystack, needle, start = 0):
        try:
            return haystack.index(needle, start)
        except ValueError:
            return -1
    i = myIndexOf(mtext, "inconnue, veuillez reformuler votre demande.")
    if i >= 0:
        lastRATPError = "Address not recognized"
        return None
    changed = False
    i = myIndexOf(mtext, "id=\"itineraire_startAddressSuggestions\">")
    if i >= 0:
        i += 40
        j = myIndexOf(mtext, "</select>", i)
        if j < 0:
            lastRATPError = "Unexpected exception (no </select>)"
            return None
        r = reRATPOption.search(mtext[i:j])
        if r is None:
            lastRATPError = "Unexpected exception (no option found)"
            return None
        origin = r.group(1)
        changed = True
    i = myIndexOf(mtext, "id=\"itineraire_endAddressSuggestions\">")
    if i >= 0:
        i += 38
        j = myIndexOf(mtext, "</select>", i)
        if j < 0:
            lastRATPError = "Unexpected exception (no </select>)"
            return None
        r = reRATPOption.search(mtext[i:j])
        if r is None:
            lastRATPError = "Unexpected exception (no option found)"
            return None
        destination = r.group(1)
        changed = True
    if changed:
        if not useSuggestions:
            lastRATPError = "Incorrect address (suggestions ignored)"
            return None
        return getDistRATP(origin, destination, timestamp, isArrivalTime, False)
    r = reRATPTime.search(mtext)
    if r is None:
        lastRATPError = "Answer not found"
        return None
    r = filter(lambda x: x in reRATPPrintable, r.group(1))
    r2 = r.replace("<span class=\"mask\">:</span>", "")
    r2 = r2.replace("&nbsp;", "")
    r2 = r2.replace("<abbr title=\"heure\">h</abbr>", "h")
    r2 = r2.replace("<abbr title=\"minute\">min</abbr>", "")
    if not reRATPSafeStr.match(r2):
        lastRATPError = "Unrecognized answer: '" + r + "'"
        return None
    if r2[-1:] == 'h':
        r2 += "0"
    r2 = r2.replace("h", "*60+")
    return int(eval(r2)) * 60

