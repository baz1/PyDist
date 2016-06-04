#!/bin/bash

if [ ! -f "google.key" ]; then
  echo "Error: Google Key missing."
  exit
fi

if [ ! -f "origins.test" ]; then
  echo "Error: Origins file missing."
  exit
fi

if [ ! -f "destinations.test" ]; then
  echo "Error: Destinations file missing."
  exit
fi

# Parameters
day=0 # 0-6, 0 is Monday
hour=8
minutes=30
ts=
type=arrive
# End of the parameters

if [ "$ts" == "" ]; then
  nday=$(date +%u)
  nhour=$(date +%H)
  nmin=$(date +%M)
  nsec=$(date +%S)
  ts=$(date +%s)
  ts=$(expr $ts + 60 - $nsec)
  ts=$(expr $ts + 60 \* \( 59 - $nmin \))
  ts=$(expr $ts + 3600 \* \( 23 - $nhour \))
  ts=$(expr $ts + 86400 \* \( \( 7 + $day - $nday \) % 7 \))
  ts=$(expr $ts + 3600 \* $hour + 60 \* $minutes)
  echo Date to $type: $(date --date=@$ts)
fi

gkey=$(head --lines=1 google.key)

echo Car calculations...
./PyDist.py "mode=car" "$type=$ts" "gapikey=$gkey" $1 "origins.test" "destinations.test" "car.test"
echo Transit calculations...
./PyDist.py "mode=transit" "$type=$ts" "gapikey=$gkey" $1 "origins.test" "destinations.test" "transit.test"
echo Done.
