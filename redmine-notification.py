#!/usr/bin/env python

import sys
from json import dump,dumps
from redmine import Redmine
import requests
import re
from time import time

def parse_arguments(argv):
    # creating empty dictionary
    event = {} 
    
    # for each pair of argument
    for i in range(1,len(argv)-1,2):
        # get rid of '--' 
        name = argv[i].replace('--','').replace('"','')
        value = argv[i+1].replace('"','')
        # and assign it to our dictonary
        event[name] = value;
    return event

def issue_create(event):
    issue = redmine.issue.create(
            project_id=project_id,
            subject=event['host.name']+" "+event['service.name'],
            description="Icinga wykryla problem: http://icinga2.radiouniwersytet.pl/icingaweb2/monitoring/host/services?host={}}&service={} Szczegóły: {}".format(event[host.name],event[service.name],dumps(event,indent=4,sort_keys=True))
    )
    return issue

def issue_find(event):
    issues = redmine.issue.filter(
            project_id=project_id,
            status_id='open',
            subject=event['host.name']+" "+event['service.name'],
            sort='created_on'
    )
    return issues

def issue_update(event,issue):
    redmine.issue.update(
        resource_id = issue.id,
        notes = dumps(event,indent=4,sort_keys=True)
    )
    return issue

def issue_close(issue):
    redmine.issue.update(
        resource_id = issue.id,
        notes = dumps(event,indent=4,sort_keys=True),
        status_id=5
    )
    return issue
    

def icinga2_add_comment(event,comment):
    r = requests.post(
        'https://127.0.0.1:5665/v1/actions/add-comment',
        params = {
            'type': 'Service',
            'filter': 'service.name=="'+event['service.name']+'"',
            'filter': 'host.name=="'+event['host.name']+'"'
        },
        data = dumps({
            'author': 'Redmine Bot', 'comment': comment
        }),
        auth = ('root','bb03db411b5d9ce1'),
        headers = {'Accept': 'application/json'},
        verify=False
    )

def icinga2_delete_comments_old(how_old):
    r = requests.post(
        'https://localhost:5665/v1/objects/comments',
        auth = ('root','bb03db411b5d9ce1'),
        headers = {'Accept': 'application/json'},
        verify=False
    )
    resp = r.json()
    for comment in resp['results']:
        comment_time = int(re.findall(".*\!icinga2-(\d{10})-\d+",comment['name'])[0])
        
        if(time()-comment_time > how_old):
            r_del = requests.post(
                'https://localhost:5665/v1/actions/remove-comment',
                params = {
                    'comment': comment['name']
                },
                auth = ('root','bb03db411b5d9ce1'),
                headers = {'Accept': 'application/json'},
                verify=False
            )
    return len(resp)

# receive and parse event from cmd line


event = parse_arguments(sys.argv)

# for debug purposes log all events in logfile
with open('/tmp/event', 'w+') as testfile:
    dump(event,testfile,indent=4,sort_keys=True)

# create redmine connection and set project 
redmine = Redmine('http://redmine.q84fh.net',version='3.2.0',key='eeedd4095a6193f0b3570243c167ce1028463c85')
project_id = 'radio-uniwersytet'

# ask redmine if some issues are already openen for our event
opened_issues = issue_find(event)

if event['notification.type'] == 'PROBLEM':
    if opened_issues:
        # if we already have an issue opened we are sending an update
        issue = issue_update(event,opened_issues[0])
        icinga2_add_comment(event,"Ticket updated: #"+str(issue.id))
    else:
        # else we creating new issue
        issue = issue_create(event)
        icinga2_add_comment(event,"Ticket opened: #"+str(issue.id))

if event['notification.type'] == 'RECOVERY':
    for issue in opened_issues:
        issue_close(issue)
        icinga2_add_comment(event,"Ticket closed: #"+str(issue.id))

# housekeeping
icinga2_delete_comments_old(604800)