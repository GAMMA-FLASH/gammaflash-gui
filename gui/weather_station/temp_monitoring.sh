#!/bin/bash

while :
do

perl check_hwg-ste2.pl -H 192.168.0.17 -S 252 >> weather_station_temp.txt
sleep 120
done

