#!/bin/env python

"""

SOAP client to query the dotmailer account and pull back any results
from campaign sends (e.g. hard bounces etc) in JSON format.

Usage: dotmailer.py <action> [<data>]

Where action is one of

     hardbounces
     listcampaigns
     query
     unsubscribers
     listaddressbooks
     getaddressbookcontactcount
     createaddressbook

and data is appropriate to the action (e.g. for 'query' you provide an
email address etc).

"""

import sys, datetime, base64

from suds.client  import Client     as SOAPClient
from django.utils import simplejson as json
from types        import *

from dotmailerauth import api_username, api_password

url              = r'http://apiconnector.com/api.asmx?WSDL'
api_username     = api_username()
api_password     = api_password()

try:
    action           = sys.argv[1]
except IndexError:
    print "Usage: dotmailer <action> [<data>]"
    sys.exit(1)

def printContactResult (result):
    myUser = {}
        
    for dataP in result:
        if type(dataP[1]) is not InstanceType:
            myUser[dataP[0]] = dataP[1]

    for fieldIdx in range(len(result.DataFields['Keys']['string'])):
        myUser["DATAFIELD--" + result.DataFields['Keys']['string'][fieldIdx]] = result.DataFields['Values'][0][fieldIdx]

    s = json.dumps(myUser, sort_keys=True, indent=4)
    print '\n'.join([l.rstrip() for l in  s.splitlines()])

def getMyCampaigns ():
    
    client      = SOAPClient(url)

    try:
        result = client.service.ListCampaigns(api_username, api_password)
    except:
        print "Campaign list fail"
    else:

        myCampaigns = []

        for campaign in result[0]:
            myCamp = {}
            for r in campaign:
                myCamp[r[0]] = r[1]

            myCampaigns.append(myCamp)

        return myCampaigns

def getMyAddressBooks ():
    
    client      = SOAPClient(url)

    try:
        result = client.service.ListAddressBooks(api_username, api_password)
    except:
        print "Address books list fail"
    else:

        myBooks = []

        for book in result[0]:
            myCamp = {}
            for r in book:
                myCamp[r[0]] = r[1]

            myBooks.append(myCamp)

        return myBooks

def getAddressBookContactCount (id):
    
    client      = SOAPClient(url)

    try:
        result = client.service.GetAddressBookContactCount(api_username, api_password, id)
    except:
        print "Address book contact count fail"
    else:
        return result

def createAddressBook (name):
    
    client      = SOAPClient(url)

    try:
        result = client.service.CreateAddressBook(api_username, api_password, { 'Name': name } )
    except:
        print "Address book create fail"
    else:
        return result

#---

if action == 'desc':
    client        = SOAPClient(url)
    print client

elif action == 'query':

    client        = SOAPClient(url)
    try:
        user_email    = sys.argv[2]
    except IndexError:
        print "Usage: dotmailer query <email_address>"
        sys.exit(1)
    else:
        try:
            result = client.service.GetContactByEmail(api_username, api_password, user_email)
        except:
            print "User " + user_email + " not found"
        else:
            printContactResult(result)
        
elif action == 'hardbounces':

    client      = SOAPClient(url)
    myUsers     = []
    myCampaigns = []

    try:
        campaignWanted = sys.argv[2]
    except IndexError:
        myCampaigns = getMyCampaigns()
    else:
        myCampaigns.append( {"Id": campaignWanted} )

    for campaign_idx in range(len(myCampaigns)):
        campaign_id = myCampaigns[campaign_idx]['Id']

        try:
            result = client.service.ListHardBouncingContacts(api_username, api_password, campaign_id)
        except:
            print "Campaign " + campaign_id + " not found"
        else:
            if len(result):
                for bouncedContact in result[0]:
                    userEmailAddress = bouncedContact[1]
                    myUsers.append(userEmailAddress)
            
    s = json.dumps(myUsers, sort_keys=True, indent=4)
    print '\n'.join([l.rstrip() for l in  s.splitlines()])

elif action == 'listcampaigns':
    
    myCampaigns = getMyCampaigns()

    s = json.dumps(myCampaigns, sort_keys=True, indent=4)
    print '\n'.join([l.rstrip() for l in  s.splitlines()])

elif action == 'listaddressbooks':
    
    myBooks = getMyAddressBooks()

    s = json.dumps(myBooks, sort_keys=True, indent=4)
    print '\n'.join([l.rstrip() for l in  s.splitlines()])

elif action == 'getaddressbookcontactcount':
    
    try:
        abid = int(sys.argv[2]) # address book id
    except:
        print "Usage: dotmailer getaddressbookcontactcount <address book id>"
        sys.exit(1)
        
    myCount = getAddressBookContactCount(abid)

    print myCount
    
elif action == 'createaddressbook':
    
    try:
        aname = sys.argv[2] # address book name
    except:
        print "Usage: dotmailer createaddressbook <address book name>"
        sys.exit(1)
        
    print createAddressBook(aname)
        
elif action == 'unsubscribers':

    client      = SOAPClient(url)
    myUsers     = []

    try:
        daysdiff = int(sys.argv[2])
    except IndexError:
        daysdiff = 90 # default is all those who unsubscribed in the past 3 months

    td = datetime.timedelta(days = daysdiff)
    d1 = datetime.datetime.now() - td

    try:
        result = client.service.ListUnsubscribers(api_username, api_password, d1)
    except:
        print "Failure retrieving unsubscribed users"
        sys.exit(1)
    else:
        if len(result):
            for bouncedContact in result[0]:
                userEmailAddress = bouncedContact[1]
                myUsers.append(userEmailAddress)
                
            s = json.dumps(myUsers, sort_keys=True, indent=4)
            print '\n'.join([l.rstrip() for l in  s.splitlines()])

elif action == 'addcontactstoaddressbook':
    try:
        addressbookid    = sys.argv[2]
        contactsfilename = sys.argv[3]
    except IndexError:
        print "Usage: dotmailer addcontactstoaddressbook addressbookid contactsfilename\n"
        sys.exit(1)

    initial_data = open(__file__, contactsfilename)
    base64_data  = base64.b64encode(initial_data)

    client = SOAPClient(url)

else:

    print "Action '" + action + "' not found."
