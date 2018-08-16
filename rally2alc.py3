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
import pytz

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

    print(search_criteria)
    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        print("error processing")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            if userStory["FormattedID"] not in prevProcessedUS:
                postWebhook(userStory)
                print(userStory["FormattedID"], userStory["LastUpdateDate"], datetime.datetime.now())
                usList.add(userStory["FormattedID"])
            #else:
            #    print("Not found {}".format(userStory["FormattedID"]))

    # Writes processed stories so they aren't processed again
    writePreviouslyProcessedUserStores(usList)
    print("Finished stories")

def setTimeFile():
    print("Entering Main")
    t = datetime.datetime.now(pytz.timezone('UTC')).isoformat()
    t = t[:-8] + "Z"    
    with open("lastrun.txt", mode="w+") as file:
        file.write("%s" % t)

def getTimeFile():
    try:
        print ("retrieving last run date")
        with open("lastrun.txt", mode="r") as file:
            lastrun = file.read().replace('\n', '')
        file.close()
        print(lastrun)
    except Exception:
        return "never"

    return lastrun

def printTime():
    t = datetime.datetime.now(pytz.timezone('UTC')).isoformat()
    t = t[:-8] + "Z"    
    print("Current time is : %s" % t)

def writePreviouslyProcessedUserStores(USList):
    conf = getConfig.getConfig()
    with open(conf.storylog, mode="a") as file:
        for us in USList:
            file.write(us)
            file.write("\n")

def readPreviouslyProcessedUserStories():
    previousUS = set()
    conf = getConfig.getConfig()
    try:
        with open(conf.storylog, mode="r") as file:
            line = file.read()
            line = line.split()
        for x in line:
            previousUS.add(x)
    except Exception:
        return previousUS

    return previousUS

def Cleanup(search_criteria):
    # Debug, clean up after testing
    print(search_criteria)
    processedUserStories = readPreviouslyProcessedUserStories()
    conf = getConfig.getConfig()
    
    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        print("Error Proccessing Cleanup")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            if userStory["FormattedID"] in processedUserStories:
                print(userStory["FormattedID"], userStory["LastUpdateDate"])
                processedUserStories.remove(userStory["FormattedID"])

    # Overwrite previous Storage file
    with open(conf.storylog, mode="w") as file:
        for us in processedUserStories:
            file.write(us)
            file.write("\n")

def main(args):
    global rally

    printTime()
    lastrun = getTimeFile()
    conf = getConfig.getConfig()

    if lastrun == "never":
        search_string = "ScheduleState = Completed"
    else:
        search_string = conf.query.format(lastrun)

    rally = Rally(conf.url, apikey=conf.api, workspace=conf.wksp, project=conf.proj)
    print("logged in")

    # Process Stories for Webhook
    getCompletedStories(search_string)
    
    # In some cases, the story will change state and you want the webhook to fire again.
    # We need to remove the US ID from the UserStory.txt file, as this is the list to skip
    # This prevents the webhook from firing if a field is updated but the status hasn't changed
    # because the Rally API doesn't allow checking previous values.
    if conf.runcleanup and lastrun != "never":
        print("Processing Cleanup Routine")
        # Call cleanup query with the last run time.
        Cleanup(conf.cleanupquery.format(lastrun))




    setTimeFile()

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

