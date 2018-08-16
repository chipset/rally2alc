import sys
import datetime
import collections
import copy
import os
import argparse
import re
import time
import json
import logging
import requests
import getConfig

from pyral import Rally, rallyWorkset


global pidfile
global rally

def postWebhook(payload):
    conf = getConfig.getConfig()
    webhook_url = "http://alc.ngrok.io/rest/eventhook?apikey=5ab1a313-af93-44e2-9e71-8dba6fd45b95&processorid=6000117"
    webhook_url = conf.endpoint
    response = requests.post(
        webhook_url, data=json.dumps(payload),
        headers= {'Content-type':'application/json'}
    )
    if response.status_code != 200:
        print("Error connecting to ALC")
    else:
        print("fired webhook")


def getCompletedStories(search_criteria):
    global rally
    #error = False
    usList = set()
    print("Getting stories")

    # Read User Stories to determine if they've been previously processed -- TODO
    prevProcessedUS = readPreviouslyProcessedUserStories()

    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        print("error")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            postWebhook(userStory)
            print(userStory["FormattedID"], userStory[LastUpdateDate])
            usList.add(userStory["FormattedID"])

    # Writes processed stories so they aren't processed again
    writePreviouslyProcessedUserStores(usList)
    print("Finished stories")

def setTimeFile():
    print("Entering Main")
    t = datetime.datetime.now().isoformat()
    t = t[:-2] + "Z"    
    with open("lastrun.txt", mode="w+") as file:
        file.write("%s" % t)

def getTimeFile():
    try:
        print ("retrieving last run date")
        with open("lastrun.txt", mode="r") as file:
            lastrun = file.read().replace('\n', '')
        file.close()
        print(lastrun)
    except FileNotFoundError:
        return "never"

    return lastrun

def printTime():
    t = datetime.datetime.now().isoformat()
    t = t[:-2] + "Z"    
    print("Current time is : %s" % t)

def writePreviouslyProcessedUserStores(USList):
    with open("UserStories.txt", mode="w+") as file:
        for us in USList:
            file.write(us)
            file.write("\n")

def readPreviouslyProcessedUserStories():
    previousUS = set()
    with open("UserStories.txt", mode="r") as file:
        line = file.read()
        line = line.split()
    for x in line:
        previousUS.add(x)
    
    return previousUS

def hasBeenProcessedUS():
    pass

def main(args):
    global rally

    printTime()
    lastrun = getTimeFile()
    conf = getConfig.getConfig()

    if lastrun == "never":
        search_string = "ScheduleState = Completed"
    else:
        search_string = conf.query.format(lastrun)

    print(conf.api)
    print(conf.url)
    rally = Rally(conf.url, apikey=conf.api, workspace=conf.wksp, project=conf.proj)
    print("logged in")

    getCompletedStories(search_string)
    setTimeFile()

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

