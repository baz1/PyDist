import requests
import time
import re
import string
import urllib
from HTMLParser import HTMLParser

lastRATPError = ""
RATPToChange = []

reRATPTime = re.compile("<dt class=\"mask\">Horaires</dt>\\s*<dd class=\"time\">\\s*" +
    "<b>((?:(?!</b>).)*)</b>")
reRATPSafeStr = re.compile("^\\d+(?:h\\d*)?$")
reRATPOption = re.compile("<option value=\"([^\"]+)\">")
reRATPPrintable = set(string.printable)

def getDistRATP(origin, destination, timestamp = None, isArrivalTime = True, useSuggestions = True):
    """
    Returns the number of seconds for the itinerary,
    None if an error happened (then read lastRATPError),
    or -1 if the address has not been recognized.
    origin: Address of origin
    destination: Address of destination
    timestamp: The arrival (or departure) timestamp
    isArrivalTime: Set it to False to indicate that timestamp is the departure time
    useSuggestions: Do we want to accept address corrections, and automatically choose the first suggestion?
    """
    global lastRATPError, reRATPTime, reRATPSafeStr, reRATPOption, reRATPPrintable, RATPToChange
    url = "http://www.ratp.fr/itineraires/fr/ratp/recherche-avancee"
    url += "?start=" + urllib.quote(origin)
    url += "&end=" + urllib.quote(destination)
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
        lastRATPError = "Status code: " + str(r.status_code) + " on URL: " + url
        return None
    mtext = r.text.encode('utf-8')
    def myIndexOf(haystack, needle, start = 0):
        try:
            return haystack.index(needle, start)
        except ValueError:
            return -1
    incquit = False
    i = myIndexOf(mtext, "t inconnue, veuillez reformuler votre demande.")
    if i >= 0:
        RATPToChange.append("RATP: origin " + origin)
        incquit = True
    i = myIndexOf(mtext, "e inconnue, veuillez reformuler votre demande.")
    if i >= 0:
        RATPToChange.append("RATP: destination " + destination)
        incquit = True
    changed = False
    i = myIndexOf(mtext, "id=\"itineraire_startAddressSuggestions\">")
    if i >= 0:
        i += 40
        j = myIndexOf(mtext, "</select>", i)
        if j < 0:
            lastRATPError = "Unexpected exception (no </select>) on URL: " + url
            return None
        r = reRATPOption.search(mtext[i:j])
        if r is None:
            lastRATPError = "Unexpected exception (no option found) on URL: " + url
            return None
        h = HTMLParser()
        origin = h.unescape(r.group(1))
        if not useSuggestions:
            RATPToChange.append("RATP: origin " + origin)
            incquit = True
        changed = True
    i = myIndexOf(mtext, "id=\"itineraire_endAddressSuggestions\">")
    if i >= 0:
        i += 38
        j = myIndexOf(mtext, "</select>", i)
        if j < 0:
            lastRATPError = "Unexpected exception (no </select>) on URL: " + url
            return None
        r = reRATPOption.search(mtext[i:j])
        if r is None:
            lastRATPError = "Unexpected exception (no option found) on URL: " + url
            return None
        h = HTMLParser()
        destination = h.unescape(r.group(1))
        if not useSuggestions:
            RATPToChange.append("RATP: destination " + destination)
            incquit = True
        changed = True
    if incquit:
        return -1
    if changed:
        return getDistRATP(origin, destination, timestamp, isArrivalTime, False)
    r = reRATPTime.search(mtext)
    if r is None:
        if myIndexOf(mtext, "Aucun trajet ne correspond") > 0:
            return -1
        lastRATPError = "Answer not found on URL: " + url
        return None
    r = filter(lambda x: x in reRATPPrintable, r.group(1))
    r2 = r.replace("<span class=\"mask\">:</span>", "")
    r2 = r2.replace("&nbsp;", "")
    r2 = r2.replace("<abbr title=\"heure\">h</abbr>", "h")
    r2 = r2.replace("<abbr title=\"heures\">h</abbr>", "h")
    r2 = r2.replace("<abbr title=\"minute\">min</abbr>", "")
    r2 = r2.replace("<abbr title=\"minutes\">min</abbr>", "")
    if not reRATPSafeStr.match(r2):
        lastRATPError = "Unrecognized answer: '" + r + "' on URL: " + url
        return None
    while r2[0] == '0':
        r2 = r2[1:]
    r3 = r2.replace("h0", "h")
    while r3 != r2:
        r2 = r3
        r3 = r2.replace("h0", "h")
    if r2[-1:] == 'h':
        r2 += "0"
    r2 = r2.replace("h", "*60+")
    return int(eval(r2)) * 60

