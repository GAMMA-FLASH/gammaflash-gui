import os
import re
import time
import pymysql
import subprocess
import numpy as np
import pymysql.cursors

ip = "192.168.176.198"
sensor = "252"
sleeptime = 120

def get_config():

    db_host = '192.168.166.79'
    db_user = 'gammaflash'
    db_pass = os.environ["DB_PASS"]
    db_port = '3306'
    db_results = 'gammaflash_test'
    db_logs = ''
    xml_config=""

    return {'db_host':db_host,'db_user':db_user,
    'db_pass':db_pass,'db_port':db_port,'db_results':db_results,'db_logs':db_logs,'xml_config':xml_config}

conf_dict = get_config()

while True:
    pipe = subprocess.run(f"perl ./check_hwg-ste2.pl -H {ip} -S {sensor}", capture_output=True, shell=True)
    result = str(pipe.stdout).split(",")
    print(result)
    timestamp = int(result[0].split(" ")[1])
    state = str(result[2].split(" ")[2])
    temp = float(re.findall(r"\d\d.\d", result[3])[0])
    print(temp)


    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    
    cursor.execute(f"INSERT INTO gammaflash_test.weather_station (Timestamp, State, Temp) VALUES({timestamp}, '{state}', {temp});")
    results = cursor.fetchall()
    conn.commit()
    time.sleep(sleeptime)



cursor.close()
conn.close()
