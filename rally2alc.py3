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
import logging

from pyral import Rally, rallyWorkset
global rally

logging.basicConfig(filename="logs/rally2alc.log", level=logging.DEBUG)

def postWebhook(payload):
    conf = getConfig.getConfig()
    webhook_url = conf.endpoint
    response = requests.post(
        webhook_url, data=json.dumps(payload),
        headers= {'Content-type':'application/json'}
    )
    if response.status_code != 200:
        logging.debug("Error connecting to Webhook server Status Code: {}".format(response.status_code))
        logging.debug("Error connecting to Webhook server Formatted ID: {}".format(payload["FormattedID"]))
    else:
        logging.debug("Successfully fired Webhook for {}".format(payload["FormattedID"]))


def getCompletedStories(search_criteria):
    global rally
    #error = False
    usList = set()
    logging.info("Getting list of completed stories.")

    # Read User Stories to determine if they've been previously processed -- TODO
    prevProcessedUS = readPreviouslyProcessedUserStories()

    logging.debug("Search Criteria: {}".format(search_criteria))
    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        logging.debug("Error processing Completed Stories")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            if userStory["FormattedID"] not in prevProcessedUS:
                postWebhook(userStory)
                logging.info("Processing {}, which was last updated on {}".format(userStory["FormattedID"], userStory["LastUpdateDate"]))
                usList.add(userStory["FormattedID"])

    # Writes processed stories so they aren't processed again
    writePreviouslyProcessedUserStores(usList)
    logging.info("Finished processing stories")

def setTimeFile():
    t = datetime.datetime.now(pytz.timezone('UTC')).isoformat()
    t = t[:-8] + "Z"    
    with open("lastrun.txt", mode="w+") as file:
        file.write("%s" % t)

def getTimeFile():
    try:
        with open("lastrun.txt", mode="r") as file:
            lastrun = file.read().replace('\n', '')
        file.close()
        logging.debug("Last run time from file: {}".format(lastrun))
    except Exception:
        return "never"

    return lastrun

def printTime():
    t = datetime.datetime.now(pytz.timezone('UTC')).isoformat()
    t = t[:-8] + "Z"    

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
    logging.debug("Searching clenaup routine. Search Criteria is: {}".format(search_criteria))
    processedUserStories = readPreviouslyProcessedUserStories()
    conf = getConfig.getConfig()
    
    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        logging.debug("Error Proccessing Cleanup Routine")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            if userStory["FormattedID"] in processedUserStories:
                logging.debug("Found {}.  It will be removed from processed story file.".format(userStory["FormattedID"]))
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
        setTimeFile()
        print("This is the first time this has run (or the timefile.txt is missing.")
        print("Setting up timefile.txt.  Program will exit.  Please restart it.")
        logging.debug("Could not find time file.  Exiting.")
        sys.exit(1)
    print("Starting Rally2ALC...")
    rally = Rally(conf.url, apikey=conf.api, workspace=conf.wksp, project=conf.proj)
    logging.debug("Logged into rally: {} Workspace: {} Project: {}".format(conf.url, conf.wksp, conf.proj))

    # Process Stories for Webhook
    getCompletedStories(conf.query.format(lastrun))
    
    # In some cases, the story will change state and you want the webhook to fire again.
    # We need to remove the US ID from the UserStory.txt file, as this is the list to skip
    # This prevents the webhook from firing if a field is updated but the status hasn't changed
    # because the Rally API doesn't allow checking previous values.
    if conf.runcleanup and lastrun != "never":
        logging.debug("Processing cleanup routine")
        # Call cleanup query with the last run time.
        Cleanup(conf.cleanupquery.format(lastrun))

    setTimeFile()
    print("Finished.")

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

