# !/usr/bin/python
'''
# Python 2.7.9 script to download the last minute of Setup Audit Trail events
# Pre-requisite: standard library functionality = e.g urrlib2, json, StringIO

 #/**
 #* Copyright (c) 2012, Salesforce.com, Inc.  All rights reserved.
 #*
 #* Redistribution and use in source and binary forms, with or without
 #* modification, are permitted provided that the following conditions are
 #* met:
 #*
 #*   * Redistributions of source code must retain the above copyright
 #*     notice, this list of conditions and the following disclaimer.
 #*
 #*   * Redistributions in binary form must reproduce the above copyright
 #*     notice, this list of conditions and the following disclaimer in
 #*     the documentation and/or other materials provided with the
 #*     distribution.
 #*
 #*   * Neither the name of Salesforce.com nor the names of its
 #*     contributors may be used to endorse or promote products derived
 #*     from this software without specific prior written permission.
 #*
 #* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 #* "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 #* LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 #* A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 #* HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 #* SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 #* LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 #* DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 #* THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 #* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 #* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 #*/
'''

#Imports

import urllib2
import json
import sys
import time
import datetime
from time import sleep
from time import localtime, strftime, gmtime
import os
#import newrelic
#import newrelic.agent

# Addition from NR Support
#curdir = os.getcwd()
#print curdir
#newrelic.agent.initialize(curdir+'/newrelic.ini')
#application = newrelic.agent.register_application(timeout=10.0)

# Configurations - change to fit your org TODO: set this in environmental variables

# Use to adjust authentication and API settings
CLIENT_ID = str(os.environ.get('CLIENT_ID'))
CLIENT_SECRET = str(os.environ.get('CLIENT_SECRET'))
USERNAME = str(os.environ.get('USERNAME'))
PASSWORD = str(os.environ.get('PASSWORD'))
SECURITYTOKEN = str(os.environ.get('SECURITYTOKEN'))
APIVERSION = str(os.environ.get('APIVERSION'))

# Use to adjust the last_modified_date filter (default last 60 seconds)
MINUTES = int(os.environ.get('MINUTES'))

# Adjust the following two to equal 600 seconds (min Scheduler job) - SLEEP in seconds
SLEEP = int(os.environ.get('SLEEP'))
#LOOP = int(os.environ.get('LOOP'))

# login function
#@newrelic.agent.background_task()
def login():
    ''' Login to salesforce service using OAuth2 '''

    # create a new salesforce REST API OAuth request
    url = 'https://login.salesforce.com/services/oauth2/token'
    data = '&grant_type=password&client_id='+CLIENT_ID+'&client_secret='+CLIENT_SECRET+'&username='+USERNAME+'&password='+PASSWORD+SECURITYTOKEN
    headers = {'X-PrettyPrint' : '1'}

    # workaround to ssl issue introduced before version 2.7.9
    #if hasattr(ssl, '_create_unverified_context'):
        #ssl._create_default_https_context = ssl._create_unverified_context
    # call salesforce REST API and pass in OAuth credentials
    req = urllib2.Request(url, data, headers)
    res = urllib2.urlopen(req)
    
    # load results to dictionary
    res_dict = json.load(res)
    # close connection
    res.close()

    # return OAuth access token necessary for additional REST API calls
    access_token = res_dict['access_token']
    instance_url = res_dict['instance_url']

    return access_token, instance_url

# download function
#@newrelic.agent.background_task()
def download_audit_events():
    ''' Query salesforce service using REST API '''  
    # login and retrieve access_token and DATETIME
    access_token, instance_url = login()
    # get the last minute to pass into the SOQL filter
    last_modified_date = last_modified()
    #print last_modified_date
    
    # query Setup Audit Trail
    url = instance_url+'/services/data/v'+ APIVERSION +'/query?q=SELECT+Action+,+CreatedBy.Name+,+CreatedBy.Profile.Name+,+CreatedBy.UserRole.Name+,+CreatedById+,+CreatedDate+,+DelegateUser+,+Display+,+Id+,+Section+FROM+SetupAuditTrail+WHERE+CreatedDate+>+'+last_modified_date+'+ORDER+BY+CreatedDate+DESC+NULLS+LAST'
    #print url
    headers = {'Authorization' : 'Bearer ' + access_token, 'X-PrettyPrint' : '1'}
    req = urllib2.Request(url, None, headers)
    res = urllib2.urlopen(req)
    res_dict = json.load(res)

    # capture record result size to loop over
    total_size = res_dict['totalSize']
    #print total_size

    # provide feedback if no records are returned
    if total_size < 1:
        print 'No Setup Audit Trail events were created since ' + last_modified_date
        #sys.exit()
   #otherwise, loop through the results and print to stdout
    else:
        for i in range(total_size):
            # pull attributes out of JSON for mapping
            ids = res_dict['records'][i]['Id']
            action = res_dict['records'][i]['Action']
            name = res_dict['records'][i]['CreatedBy']['Name']
            profile = res_dict['records'][i]['CreatedBy']['Profile']['Name']
            role = res_dict['records'][i]['CreatedBy']['UserRole']['Name']
            userId = res_dict['records'][i]['CreatedById']
            createddate = res_dict['records'][i]['CreatedDate']
            #delegateuser = res_dict['records'][i]['DelegateUser']
            display = res_dict['records'][i]['Display']
            section = res_dict['records'][i]['Section']

            # print log message
            print 'Setup Audit Trail Record' + \
            ' | ' + 'Event Time: ' + createddate + \
            ' | ' + 'User Name: ' +  name + \
            ' | ' + 'User Profile: ' +  profile + \
            ' | ' + 'User Role: ' +  role + \
            ' | ' + 'Display: ' +  display + \
            ' | ' + 'Section: ' +  section + \
            ' | ' + 'Action: ' +  action + \
            ' | ' + 'Record Id : ' +  ids
            #' | ' + 'Delegated User : ' +  delegateuser 

    # close connection
    res.close

#@newrelic.agent.background_task()
def last_modified():
    ''' Last Modified function for getting the timestamp SECONDS seconds ago for SOQL filtering '''
  
    # get the time right now in local time
    datetime_now = datetime.datetime.utcnow()
    #print datetime_now
    # get the time one minute ago in utc time
    one_minute = datetime_now - datetime.timedelta(minutes=MINUTES)
    # format the last modified by date to work with SOQL
    last_modified_date = one_minute.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # return the last_modified_date (e.g. 2015-08-27T18:55:47.000Z) to the calling function
    return last_modified_date

# main function
#@newrelic.agent.background_task()
def main():
    ''' Main function '''

    # try to loop once per minute for ten minutes 
    try:
        # loop up to 10 minutes (min Scheduler time)
        x = 0
        while True: 
            # download last set of Setup Audit Trail events
            download_audit_events()

            # sleep  before starting next loop
            #start = time.time()
            sleep(SLEEP)
            #end = time.time()
            #secs = end - start
            #print secs
            x = x + 1
            #print 'loop #: %f' % x
    # otherwise, throw an exception
    except Exception:
        print "Exception thrown at (localtime): " + strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())
        pass

if __name__ == "__main__":
    main()
