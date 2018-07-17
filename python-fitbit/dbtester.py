#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################
#                                                          #
# Simple script to connect to a remote mysql database      #
#                                                          #
#                                                          #
# Install MySQLdb package by running:                      #
#                                                          #
#                       pip install MySQL-python           #
#                                                          #
############################################################

import json
import datetime
import MySQLdb as db
import MySQLdb.cursors as cursors

import json
import fitbit
import requests
import base64
import sys
import traceback


class FitbitTimeSet:
    def __init__(self, heart_rate=0, step_count=0, activity_level=0, uid="***NO UID SUPPLIED***"):
        self.heart_rate = heart_rate
        self.step_count = step_count
        self.activity_level = activity_level
        self.uid = uid

    def __repr__(self):
        return "FitbitTimeSet(" + str(self.heart_rate) + ',' + str(self.step_count) + ',' + str(self.activity_level) + ',' + self.uid + ")"


class FitbitWeightSet:
    def __init__(self, weight=0, bmi=0, fat=0, source="", uid="***NO UID SUPPLIED***"):
        self.weight = weight
        self.bmi = bmi
        self.fat = fat
        self.source = source
        self.uid = uid

    def __repr__(self):
        return "FitbitWeightSet(" + str(self.weight) + ',' + str(self.bmi) + ',' + str(self.fat) + ',' + str(self.source) + ',' + self.uid + ")"


class DeviceInfo:
    def __init__(self, uid, device_id, last_sync_time, device_version, device_type, battery, battery_level):
        self.uid = uid
        self.device_id = device_id
        self.last_sync_time = last_sync_time
        self.device_version = device_version
        self.device_type = device_type
        self.battery = battery
        self.battery_level = battery_level

    def __repr__(self):
        return "DeviceInfo(" + str(self.uid) + ',' + str(self.last_sync_time) + ',' + str(self.device_version) + ',' + str(self.battery_level) + ")"


# These are the secrets etc from Fitbit developer
OAuthTwoClientID = "22CMWS"
ClientOrConsumerSecret = "83418e86bc034c4f162277e411144aaa"
base64_key_secret = base64.b64encode(OAuthTwoClientID + ":" + ClientOrConsumerSecret)

# This is the Fitbit URL
TokenURL = "https://api.fitbit.com/oauth2/token"

# Remote database info
HOST = "10.162.80.9"
PORT = 3306
USER = "fitbitter"
PASSWORD = "yiGLeVihDHhQMJPo"
DB = "mmcfitbit"

now = str(datetime.datetime.now())
file_name = "/Users/anthony/Desktop/python_api_puller/python-fitbit/token.json"
file_name = "token.json"

token_pair = {"access_token" : "at1", "refresh_token" : "rf1", "time" : now}

debug_flag = False


def read():
    print("Reading from existing token file...")
    file_obj = open(file_name, 'r')
    # s = file_obj.read()
    st = json.load(file_obj)
    a_token = st["access_token"]
    r_token = st["refresh_token"]
    # print('\n' + a_token + " / " + r_token)
    file_obj.close()
    print("\t...Done reading token file.")
    return {"access_token":a_token, "refresh_token":r_token}


def write():
    print("Writing...")
    
    file_obj = open(file_name, 'wb')
    # file_obj.write("access" + "\n")
    # file_obj.write("refresh" + "\n")
    # print(json.dumps(my))
    json.dump(token_pair, file_obj)
    file_obj.close()

    print("\t...Done writing!")

############################################################
#                                                          #
# Fitbit API Authorization Functions                       #
#                                                          #
############################################################


def token_authorize():
    print("Authorizing...")
    
    AuthorisationCode = sys.argv[1]
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}

    BodyText = {'code' : AuthorisationCode,
            'redirect_uri' : 'https://jhprohealth.app/callback',
            'client_id' : OAuthTwoClientID,
            'grant_type' : 'authorization_code'}

    r = requests.post(TokenURL, headers=headers, data=BodyText)
    # print(r.text)
    file_obj = open("token.json", 'wb')
    file_obj.write(r.text)
    file_obj.close()
    print("\t...Done authorizing")
    return json.loads(r.text)


def token_refresh(token_dict):
    print("Refreshing...")
    
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}

    BodyText = {
            'refresh_token' : token_dict["refresh_token"],
            'grant_type' : 'refresh_token'}
    # print('\t' + str(BodyText))

    r = requests.post(TokenURL, headers=headers, data=BodyText)
    # print(r.text)
    file_obj = open("token.json", 'wb')
    file_obj.write(r.text)
    file_obj.close()
    print("\t...Done refreshing")
    return json.loads(r.text)

def register_new_auth_code():
    print("Authorizing...")
    
    AuthorisationCode = sys.argv[1]
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}

    BodyText = {'code' : AuthorisationCode,
            'redirect_uri' : 'https://jhprohealth.app/callback',
            'client_id' : OAuthTwoClientID,
            'grant_type' : 'authorization_code'}

    r = requests.post(TokenURL, headers=headers, data=BodyText)
    if(r.status_code != 200):
        print(r.text)
        raise Exception("While registering new user, HTTP returned code ", str(r.status_code))

    response = json.loads(r.text)
    # print(r.text)
    read_token = open("token.json", 'r')
    current_user_token = json.load(read_token)
    read_token.close()

    try:
        read_mult_tokens = open("tokens.json", 'r')
        json_user_datas = json.load(read_mult_tokens)
        read_mult_tokens.close()

        if(response["user_id"] != None):
            write_file = open("tokens.json", 'w+')
            response["modified_at"] = str(datetime.datetime.now())
            json_user_datas["users"][response["user_id"]] = response
            json_user_datas["global_refresh_token"] = response["refresh_token"]
            json.dump(json_user_datas, write_file, indent=4)
            write_file.close()
    except IOError as e:
        print(e)

    
    print("\t...Done authorizing new user: " + response["user_id"])
    return json_user_datas

def get_multi_token_dict():
    print("Reading in from existing tokens.json ...")
    file_obj = open("tokens.json", 'r')
    st = json.load(file_obj)
    file_obj.close()
    print("\t...Done reading tokens.json.")
    return st


def refresh_multi_user_token(token_dict):
    json_user_datas = token_dict
    for user in json_user_datas["users"]:
        print("Pulling user : " + str(json_user_datas["users"][user]["user_id"]))
        headers = {'Authorization':'Basic ' + base64_key_secret,
                   'Content-Type':'application/x-www-form-urlencoded'}
        print("Using refresh_token -> " + str(json_user_datas["global_refresh_token"]))
        BodyText = {
                'refresh_token' : json_user_datas["users"][user]["refresh_token"],
                'grant_type' : 'refresh_token'}
        r = requests.post(TokenURL, headers=headers, data=BodyText)
        # print(r.status_code)
        # print(r.text)
        # print('\n========\n')


        if(r.status_code != 200):
            print(r.text)
            raise Exception("While refreshing user " + user + " , HTTP returned code ", str(r.status_code))
        else:
            # print(r.text)
            response = json.loads(r.text)
            # json_user_datas["global_refresh_token"] = response["refresh_token"]
            json_user_datas["users"][user]["access_token"] = response["access_token"]
            json_user_datas["users"][user]["refresh_token"] = response["refresh_token"]
            json_user_datas["users"][user]["modified_at"] = str(datetime.datetime.now())
            data_retrieval_routine(json_user_datas, user)
            # for i in range(0,7):
            #     loop_data_retrieval_routine(json_user_datas, user, i)

    write_file = open("tokens.json", 'w+')
    json.dump(json_user_datas, write_file, indent=4)
    write_file.close()

    print("\t...Done refreshing")
    return json_user_datas


def data_retrieval_routine(token_dict, uid):
    yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)
    date_string = str(yesterday.date())
    # date_string = "2018-06-01"
    try:
        print("Data retrieval routine for user: " + uid)
        device_dict = make_device_dict_from_json(get_devices(token_dict, uid), uid)
        update_devices(device_dict)
        execute_heart_and_step(token_dict, uid, date_string, device_dict)
        execute_weight(token_dict, uid, date_string)
        execute_user_info(token_dict, uid)
    except ValueError as ve:
        print ve

    print "\t-------data as of yesterday that is: " + str(yesterday.date()) + "-------"


def loop_data_retrieval_routine(token_dict, uid, days_ago):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    date_string = str(yesterday.date())
    # date_string = "2018-06-01"
    try:
        # execute_heart_and_step(token_dict, uid, date_string)
        execute_weight(token_dict, uid, date_string)

    except ValueError as ve:
        print ve

    print "\t-------data as of: " + str(yesterday.date()) + "-------"

def execute_user_info(token_dict, uid):
    user_json = get_user(token_dict, uid)
    if debug_flag:
        print(user_json)
    insert_user_info(user_json)

def insert_user_info(user_json):
    insert_set = []

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        user = user_json["user"]
        dbhandler = connection.cursor()
        stmt = "UPDATE PC_Users SET height=%s WHERE fitbit_uid='%s'" % (user["height"], user["encodedId"])
        dbhandler.execute(stmt)

    except Exception as e:
        print "EXCEPTION IN insert_user_info: " + str(e)
        print(dbhandler._last_executed)


    finally:
        connection.commit()
        connection.close()





def execute_heart_and_step(token_dict, uid, date_string, device_dict):

    heart_json = get_intraday_heart(token_dict=token_dict, uid=uid, query_date=date_string)
    step_json = get_intraday_activity(token_dict=token_dict, uid=uid, query_date=date_string)
        
    sedentary_payload =  get_activity_details(token_dict=token_dict, uid=uid, query_date=date_string, activity_resource_path="minutesSedentary")
    light_active_payload = get_activity_details(token_dict=token_dict, uid=uid, query_date=date_string, activity_resource_path="minutesLightlyActive")
    fairly_active_payload = get_activity_details(token_dict=token_dict, uid=uid, query_date=date_string, activity_resource_path="minutesFairlyActive")
    very_active_payload = get_activity_details(token_dict=token_dict, uid=uid, query_date=date_string, activity_resource_path="minutesVeryActive")
    activity_dict = combine_activity_levels(
        sedentary_payload, light_active_payload, fairly_active_payload, very_active_payload)
    
    time_dict = make_intraday_dict_from_json_datas(heart_json, step_json, activity_dict, device_dict, uid)
    insert_intraday_dict(time_dict)


def execute_weight(token_dict, uid, date_string):
    weight_data = get_weight_log(token_dict, uid, date_string)
    weight_dict = make_weight_dict_from_json(weight_data, uid, date_string)
    insert_weight_dict(weight_dict)


def multi_login_routine():
    if(len(sys.argv) == 2):
        print("Registering a new user with given AUTH CODE.")
        token_dict = register_new_auth_code()
    elif(len(sys.argv) == 1):
        print("Populating data by refreshing previous token sessions.")
        token_dict = get_multi_token_dict()
        refresh_multi_user_token(token_dict)
    elif(len(sys.argv) == 3):
        if(sys.argv[1] == "loop"):
            # token_dict = get_multi_token_dict()
            # for i in range(0, sys.argv[2]):
            exit()

    else:
        print("Needs one or no argument")
        sys.exit()
    # token_dict = token_refresh(token_dict)
    return token_dict


def login_routine():
    if(len(sys.argv) == 2):
        print("Logging in with given AUTH CODE.")
        token_dict = token_authorize()
    elif(len(sys.argv) == 1):
        print("Logging in with previous token session.")
        token_dict = read()
    else:
        print("Needs one or no argument")
        sys.exit()
    token_dict = token_refresh(token_dict)
    return token_dict


############################################################
#                                                          #
# Fitbit API calling functions                             #
#                                                          #
############################################################


def get_user(token_dict, uid):
    print("Getting user info")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/profile.json",
                      headers=headers)
    if debug_flag:
        print(r.text)
    user_json = json.loads(r.text)
    uid = user_json["user"]["encodedId"]
    # print(uid)
    print("\t...Done getting user info")

    return user_json

def get_devices(token_dict, uid):
    print("Getting Devices")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/devices.json", headers=headers)
    # print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting device info")

    return r.text

def get_body_fat_log(token_dict, uid):
    print("Getting body fat log")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/body/log/fat/date/2018-04-01/2018-04-29.json',
                      headers=headers)
    # print(r.text)
    print("\t...Done getting body fat log")

    return r.text

def get_weight_log(token_dict, uid, query_date):
    print("Getting weight log for " + query_date)
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/body/log/weight/date/%s/1d.json' % query_date,
                      headers=headers)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")

    print("\t...Done getting weight log")

    return r.text

def get_activity_details(token_dict, uid, query_date, activity_resource_path):
    print("Getting activity details")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/%s/date/%s/1d.json' % (activity_resource_path, query_date),
                      headers=headers)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    
    return r.text

def get_activities(token_dict, uid, query_date):
    print("Getting activity list")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/date/%s.json' % query_date,
                      headers=headers)
    # print(r.text)
    return r.text

def get_intraday_heart(token_dict, uid, query_date):
    print("Getting Intraday HR")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/activities/heart/date/" + query_date + "/1d/1min.json",
                      headers=headers)
    # print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting intraday heartrate")

    return r.text


def get_intraday_activity(token_dict, uid, query_date):
    print("Getting Intraday Activity in Steps")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}

    r = requests.get("https://api.fitbit.com/1/user/-/activities/steps/date/" + query_date + "/1d.json",
                      headers=headers)
    # print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting intraday steps")

    return r.text

############################################################
#                                                          #
# Database Manipulation Functions                          #
#                                                          #
############################################################


def combine_activity_levels(sedentary_payload, light_active_payload, fairly_active_payload, very_active_payload):
    print("Converting Activity Level JSON data to dictionary...")
    activity_level_dict = dict()
    if(sedentary_payload != ""):
        activity_level_dict["sedentary"] = json.loads(sedentary_payload)
    if(light_active_payload != ""):
        activity_level_dict["lightly"] = json.loads(light_active_payload)
    if(fairly_active_payload != ""):
        activity_level_dict["fairly"] = json.loads(fairly_active_payload)
    if(very_active_payload != ""):
        activity_level_dict["very"] = json.loads(very_active_payload)

    print("\t...Done Converting Activity Level JSON data to dictionary")

    return activity_level_dict


def make_intraday_dict_from_json_datas(heart_rate_json, step_count_json, activity_level_dict, device_dict, uid):

    def has_synced_yesterday(device_info_dict):
        print("HAS SYNCED RECENTLY?: " + str(device_info_dict.values()))
        for device_info in device_info_dict.values():
            print(device_info)
            if device_info.device_type == "TRACKER":
                dt = datetime.datetime.strptime(device_info.last_sync_time, "%Y-%m-%dT%H:%M:%S.%f")
                if dt < (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0):
                    print("Hasn't synced recently. Last sync time: " + str(device_info.last_sync_time))
                    return False
                else:
                    print("Has synced recently. Last sync time: " + str(device_info.last_sync_time))
                    return True
        print("\tNo tracker to calculate last synced time. Check if this person has a tracker assigned.")
        return False
    print("Converting HR and Step JSON data to dictionary...")

    heart_rates = json.loads(heart_rate_json)
    step_counts = json.loads(step_count_json)
    sed_json = activity_level_dict["sedentary"]
    lightly_json = activity_level_dict["lightly"]
    fairly_json = activity_level_dict["fairly"]
    very_json = activity_level_dict["very"]
    time_pair = dict()

    for one_day_hr in heart_rates["activities-heart"]:
        date = heart_rates["activities-heart"][0]["dateTime"]
        hr_array = heart_rates["activities-heart-intraday"]
        hr_dataset = hr_array["dataset"]
        print(hr_dataset)
        print("HR_DATASET LENGTH: " + str(len(hr_dataset)))
        if len(hr_dataset) < 1:
            if not has_synced_yesterday(device_dict):
                print("Hasn't synced yesterday. Sending ping to Non-compliance table")
                insert_noncompliance_ping(uid, date)
                raise ValueError(
                    "_ValueError: This account hasn't been synced recently. Sending ping to Non-compliance table")
            else:
                print("HR Dataset for selected date is empty. Checking if steps is also empty")
                if int(step_counts["activities-steps"][0]["value"]) < 1:
                    print("STEP Dataset for selected date is empty. Sending ping to Non-compliance table")
                    insert_noncompliance_ping(uid, date)
                    raise ValueError("Both HR and Step Dataset for selected date are empty. Sending ping to Non-compliance table")
        for data in hr_dataset:
            dtstring = date + " " + data["time"]
            if(dtstring not in time_pair):
                time_pair[dtstring] = FitbitTimeSet(data["value"], 0, 0, uid)
            else:
                time_pair[dtstring].heart_rate = data["value"]
        print("\t" + str(len(hr_dataset)) + " is the total heart rate timestamps in selected date: ")

    for one_day_steps in step_counts["activities-steps"]:
        date = step_counts["activities-steps"][0]["dateTime"]
        hr_array = step_counts["activities-steps-intraday"]
        hr_dataset = hr_array["dataset"]
        for data in hr_dataset:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"]
                if(dtstring not in time_pair):
                    time_pair[dtstring] = FitbitTimeSet(0, data["value"], 0, uid)
                else:
                    time_pair[dtstring].step_count = data["value"]

    if(sed_json["activities-minutesSedentary"][0]["value"] != 0):
        date = sed_json["activities-minutesSedentary"][0]["dateTime"]
        for data in sed_json["activities-minutesSedentary-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 1

    if(lightly_json["activities-minutesLightlyActive"][0]["value"] != 0):
        date = lightly_json["activities-minutesLightlyActive"][0]["dateTime"]
        for data in lightly_json["activities-minutesLightlyActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 2

    if(fairly_json["activities-minutesFairlyActive"][0]["value"] != 0):
        date = fairly_json["activities-minutesFairlyActive"][0]["dateTime"]
        for data in fairly_json["activities-minutesFairlyActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 3

    if(very_json["activities-minutesVeryActive"][0]["value"] != 0):
        date = very_json["activities-minutesVeryActive"][0]["dateTime"]
        for data in very_json["activities-minutesVeryActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 4

    print("\t...Done converting JSON data to dictionary")

    return time_pair

def make_weight_dict_from_json(weight_payload, uid, date_string):
    weight_json = json.loads(weight_payload)

    time_pair = dict()

    for weight_data in weight_json["weight"]:
        if(weight_data["date"] != date_string):
            continue
        if debug_flag:
            print(weight_data)
        date = weight_data["date"]
        time = weight_data["time"]
        dtstring = date + " " + time


        weight = weight_data["weight"]
        bmi = weight_data["bmi"]
        if "fat" in weight_data:
            fat = weight_data["fat"]
        else:
            fat = 0
        source = weight_data["source"]

        time_pair[dtstring] = FitbitWeightSet(weight=weight, bmi=bmi, fat=fat, source=source, uid=uid)

    return time_pair


def make_device_dict_from_json(devices_payload, uid):
    device_json = json.loads(devices_payload)

    device_id_pair = dict()

    for device_data in device_json:
        # print(device_data)
        device_id = device_data["id"]
        last_sync_time = device_data["lastSyncTime"]
        device_version = device_data["deviceVersion"]
        device_type = device_data["type"]
        battery = device_data["battery"]
        battery_level = device_data["batteryLevel"]

        device_id_pair[device_id] = DeviceInfo(uid=uid, device_id=device_id, last_sync_time=last_sync_time,
                                               device_version=device_version, device_type=device_type,
                                               battery=battery, battery_level=battery_level)
    return device_id_pair


def update_devices(device_id_pair):
    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        cursor = connection.cursor(db.cursors.DictCursor)
        result = cursor.execute("SELECT * FROM PC_Devices")
        now_time = str(datetime.datetime.now())
        # print(now_time)
        rows = cursor.fetchall()
 
        for device_id in device_id_pair:
            # print(row["submitted_at"] < datetime.datetime.now())
            print("DEVICE : " + device_id)
            device = device_id_pair[device_id]
            result = cursor.execute("INSERT INTO PC_Devices \
                (fitbit_uid, device_id, last_sync_time, device_version, device_type, battery, battery_level, updated_at)\
                VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')\
                ON DUPLICATE KEY UPDATE last_sync_time='%s', battery='%s', battery_level='%s', updated_at='%s'"
                                    % (device.uid, device_id, device.last_sync_time, device.device_version,
                                       device.device_type, device.battery, device.battery_level, now_time,
                                       device.last_sync_time, device.battery, device.battery_level, now_time))
    except Exception as e:
        print(e)
 
    finally:
        cursor.close()
        connection.commit()
        connection.close()

def insert_weight_dict(time_pair):
    insert_set = []
    for time in time_pair:
        fitbit_data = time_pair[time]
        # print(str(time) + " / " + str(fitbit_data))
        insert_set.append((time, fitbit_data.uid, fitbit_data.weight, fitbit_data.bmi, fitbit_data.fat, fitbit_data.source, str(datetime.datetime.now())))

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = "INSERT INTO PC_Weight (timestamp, fitbit_uid, weight, bmi, fat, source, added_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        dbhandler.executemany(stmt, insert_set)

    except Exception as e:
        print "EXCEPTION IN insert_weight_dict: " + str(e)

    finally:
        connection.commit()
        connection.close()




def insert_intraday_dict(time_pair):

    insert_set = []
    for time in time_pair:
        fitbit_data = time_pair[time]
        # print(str(time) + " / " + str(fitbit_data))
        insert_set.append((time, fitbit_data.uid, fitbit_data.heart_rate, fitbit_data.step_count, fitbit_data.activity_level, str(datetime.datetime.now())))

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = "INSERT INTO PC_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s)"
        dbhandler.executemany(stmt, insert_set)

    except Exception as e:
        print "EXCEPTION IN insert_intraday_dict: " + str(e)

    finally:
        connection.commit()
        connection.close()

def temp_insert_intraday_dict(time_pair):
    insert_set = []
    for time in time_pair:
        fitbit_data = time_pair[time]
        # print(str(time) + " / " + str(fitbit_data))
        insert_set.append((time, fitbit_data.uid, fitbit_data.heart_rate, fitbit_data.step_count, fitbit_data.activity_level, str(datetime.datetime.now())))

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = "INSERT INTO Temp_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s)"
        dbhandler.executemany(stmt, insert_set)

    except Exception as e:
        print "EXCEPTION IN temp_insert_intraday_dict: " + str(e)

    finally:
        connection.commit()
        connection.close()

def insert_noncompliance_ping(user_id, ping_date):
    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = """INSERT INTO PC_Noncompliance_Ping (date, fitbit_uid, not_equipped_flag, added_on) VALUES (%s, %s, %s, %s)"""

        dbhandler.execute(stmt, (ping_date, user_id, 1, str(datetime.datetime.now())))

    except Exception as e:
        print "EXCEPTION IN insert_noncompliance_ping: " + str(e)

    finally:
        connection.commit()
        connection.close()


def connect_db():
    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        dbhandler.execute("SELECT * from FitbitArchiveHeartRate")
        dbhandler.execute("")
        result = dbhandler.fetchall()
        for item in result:
            print item


    except Exception as e:
        print e

    finally:
        connection.commit()
        connection.close()





def devtestground():
    token = login_routine()
    fitbit_user_id = get_user(token)
    yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)
    date_string = str(yesterday.date())
    # TODO: ASSIGN WEIGHTED VALUES FOR ACTIVITIES
    # print(get_weight_log(token))
    weight_dict = make_weight_dict_from_json(get_weight_log(token, date_string), fitbit_user_id)
    # print(weight_dict)
    insert_weight_dict(weight_dict)

def hr_step_check():
    token = login_routine()
    fitbit_user_id = get_user(token)
    yesterday = datetime.datetime.now() - datetime.timedelta(days = 1)
    date_string = str(yesterday.date())
    # date_string = "2018-06-01"
    try:
        heart_json = get_intraday_heart(token, date_string)
        step_json = get_intraday_activity(token, date_string)
        print(heart_json)
        print(step_json)

    except ValueError as ve:
        print ve

    print "\t-------data as of: " + str(yesterday.date()) + "-------"


def get_query_start_date(uid):
    def get_db_last_hr_record():
        try:
            connection = db.Connection(host=HOST, port=PORT,
                                       user=USER, passwd=PASSWORD, db=DB,
                                       cursorclass=cursors.SSCursor)
            dbhandler = connection.cursor(cursors.DictCursor)
            stmt = "SELECT * FROM PC_Step_HeartRate WHERE fitbit_uid = '%s' ORDER BY timestamp DESC LIMIT 1" % uid
            dbhandler.execute(stmt)
            for row in dbhandler:
                return row["timestamp"]
            return None
        except Exception as e:
            traceback.print_exc()
            print "EXCEPTION get_db_last_hr_record: " + str(e)
        finally:
            connection.close()
    result = get_db_last_hr_record()
    if result is None or result.date() >= datetime.date.today() - datetime.timedelta(days=1):
        return "0"
    else:
        return result.date() + datetime.timedelta(days=1)


print("===============================================================")

print("Logging event at: " + str(datetime.datetime.now()))
# token = multi_login_routine()
# result = get_query_start_date("5TQ66D")
print get_query_start_date("5T82TY")
print (datetime.date.today() - get_query_start_date("5T82TY")).days
# print result
print("===============================================================")