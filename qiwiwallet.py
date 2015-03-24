# -*- coding: utf-8 -*-

from string import Template 
import pycurl
import argparse
import base64
import json
from io import BytesIO
import logging
import urllib
import datetime

auth_parms = {
    'provider_id': 'id', #provider id given by QIWI
    'login': 'login', #API login
    'password':  'pass' #API pass
}

auth = Template('$login:$password')
url = Template('https://w.qiwi.com/api/v2/prv/$provider_id/bills/$bill_id')
auth_encoded = base64.b64encode(auth.substitute(login=auth_parms.get('login'),password=auth_parms.get('password')))
auth_header = Template('Authorization: Basic $auth_encoded')
bill_term = 10 #срок действия счета

def check_bill_status (bill_id):
    "gets bill status from qiwi wallet system"
    response = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=bill_id))
    c.setopt(c.WRITEFUNCTION, response.write)
    c.setopt(c.HTTPHEADER, ['Accept: text/json',
                             'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                             auth_header.substitute(auth_encoded=auth_encoded)])
    c.perform()
    responseCode = c.getinfo(c.HTTP_CODE)
    json_response = json.loads(response.getvalue())
    if json_response["response"]["result_code"]:
        message = str(json_response["response"]["description"])
    elif json_response["response"]["bill"]:
        message = str(json_response)

    return message

def create_bill (user, amount, comment, bill_id, account):
    "creates bill"
    response = BytesIO()
    params = {'user': 'tel:+' + str(user), 
              'amount': amount,
              'ccy': 'RUB',
              'comment': comment,
              'lifetime': (datetime.datetime.now() + datetime.timedelta(days=10)).replace(microsecond=0).isoformat(),
              'prv_name': 'STEL',
              'pay_source':'qw',
              'account':account}              

    c = pycurl.Curl()
    c.setopt(c.CUSTOMREQUEST, "PUT")
    c.setopt(c.POSTFIELDS, urllib.urlencode(params))
    c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=bill_id))
    c.setopt(c.WRITEFUNCTION, response.write)
    c.setopt(c.HTTPHEADER, ['Accept: text/json',
                             'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                             auth_header.substitute(auth_encoded=auth_encoded)])    
    c.perform()a
    responseCode = c.getinfo(c.HTTP_CODE)
    json_response = json.loads(response.getvalue())
    message = str(json_response)    
    return message


#print create_bill("380634948892", "10.00", "test", "BILL-1")
#print create_bill("79031234567", "10.00", "test", "BILL-1", "test0001")
print check_bill_status("BILL-1")
