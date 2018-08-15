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

#from ConfigParser import SafeConfigParser
from pyral import Rally, rallyWorkset


global pidfile
global rally

def postWebhook(payload):
    webhook_url = "http://alc.ngrok.io/rest/eventhook?apikey=5ab1a313-af93-44e2-9e71-8dba6fd45b95&processorid=6000117"

    response = requests.post(
        #webhook_url, data=json.dumps(payload),
        webhook_url, data=payload,
        headers= {'Content-type':'application/json'}
    )
    if response.status_code != 200:
        print("Error connecting to ALC")
    else:
        print("fired webhook")


def getCompletedStories(t):
    global rally
    #error = False
    usList = set()
    print("Getting stories")
    fields ="Name,Owner,State,FormattedID,oid,ScheduleState,Expedite"  #add bypass sonarqube
    search_criteria = '((ScheduleState = Completed) AND (LastUpdateDate > "%s"))' % t
    print (search_criteria)
    collection = rally.get('Story', fetch=True, query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        print("error")
        sys.exit(1)
    if not collection.errors:
        content = collection.content
        for userStory in content["QueryResult"]["Results"]:
            print(userStory)
            postWebhook(userStory)
        for story in collection:
            name = '%s' % story.FormattedID
            time = '%s' % story.LastUpdateDate
            usList.add(name)
            print (name, time)
            postWebhook(name)

    writePreviouslyProcessedUserStores(usList)
    print("Finished stories")

def setTimeFile():
    print("Entering Main")
    t = datetime.datetime.now().isoformat()
    t = t[:-2] + "Z"    
    with open("lastrun.txt", mode="w+") as file:
        file.write("%s" % t)

def getTimeFile():
    print ("retrieving last run date")
    with open("lastrun.txt", mode="r") as file:
        lastrun = file.read().replace('\n', '')
    file.close()
    print(lastrun)
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
    rally = Rally('rally1.rallydev.com', 'thomas.mcquitty@integrations.acme.com', 'Kanban!!', workspace='thomas.mcquitty@ca.com-2017-05-May', project='Shopping Team')
    print("logged in")

    getCompletedStories(lastrun)
    setTimeFile()

if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

