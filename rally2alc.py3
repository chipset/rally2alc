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

#from ConfigParser import SafeConfigParser
from pyral import Rally, rallyWorkset


global pidfile
global rally

def create_pid():
    pass

def close_pid():
    pass

def getCompletedStories(t):
    global rally
    #error = False

    print("Getting stories")
    fields ="Name,Owner,State,FormattedID,oid,ScheduleState,Expedite"  #add bypass sonarqube
    search_criteria = '((ScheduleState = Completed) AND (LastUpdateDate > "%s"))' % t
    collection = rally.get('Story', query=search_criteria)
    assert collection.__class__.__name__ == 'RallyRESTResponse'
    if collection.errors:
        print("error")
        sys.exit(1)
    if not collection.errors:
        for story in collection:
            name = '%s' % story.FormattedID
            time = '%s' % story.LastUpdateDate
            print (name, time)
    print("Finished stories")

def setTimeFile(t):
    with open("lastrun.txt", mode="w+") as file:
        file.write("%s" % t)

def main(args):
    global rally

    print("Entering Main")
    t = datetime.datetime.now().isoformat()
    t = t[:-2] + "Z"

    setTimeFile(t)
    rally = Rally('rally1.rallydev.com', 'thomas.mcquitty@integrations.acme.com', 'Kanban!!', workspace='thomas.mcquitty@ca.com-2017-05-May', project='Shopping Team')
    print("logged in")

    getCompletedStories(t)


if __name__ == '__main__':
    main(sys.argv[1:])
    sys.exit(0)

