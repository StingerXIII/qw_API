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
from qiwi_auth import auth_parms

#auth_parms syntax:
#auth_parms = {
#    'provider_id': '',
#    'login': '',
#    'password':  ''
#}

#defining API functions wrappers

def create_bill (args):
    "creates bill for defined user and sum, with specified comment and ID"
    response = BytesIO()
    params = {'user': 'tel:+' + str(args.user), 
              'amount': args.amount,
              'ccy': 'RUB',
              'comment': 'bill ' + str(args.bill) + ' created by billing system',
              'lifetime': (datetime.datetime.now() + datetime.timedelta(days=10)).replace(microsecond=0).isoformat(),
              'prv_name': 'STEL',
              'pay_source': 'qw',
              'account': args.account}              
    c = pycurl.Curl()
    c.setopt(c.CUSTOMREQUEST, "PUT")
    c.setopt(c.POSTFIELDS, urllib.urlencode(params))
    c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=args.bill))
    c.setopt(c.WRITEFUNCTION, response.write)
    c.setopt(c.HTTPHEADER, ['Accept: text/json',
                             'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                             auth_header.substitute(auth_encoded=auth_encoded)])    
    c.perform()
    responseCode = c.getinfo(c.HTTP_CODE)

    try:
      message = '\nJSON Response:\n' + str(json.loads(response.getvalue()))
    except ValueError: 
      message = '\nno JSON response'

    if response != 200:
      raise QiwiApiException('HTTP Status: ' + str(responseCode) + message)

    return message

def check_bill_status (args):
    "gets bill status from qiwi wallet system"
    response = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=args.bill))
    c.setopt(c.WRITEFUNCTION, response.write)
    c.setopt(c.HTTPHEADER, ['Accept: text/json',
                             'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                             auth_header.substitute(auth_encoded=auth_encoded)])
    c.perform()
    responseCode = c.getinfo(c.HTTP_CODE)
    try:
      message = '\nJSON Response:\n' + str(json.loads(response.getvalue()))
    except ValueError: 
      message = '\nno JSON response'

    if response != 200:
      raise QiwiApiException('HTTP Status: ' + str(responseCode) + message)

    return message

def reject_bill(args):
  "rejects bill by ID"
  response = BytesIO()
  params = {'status':'rejected'}
  c = pycurl.Curl()
  c.setopt(c.CUSTOMREQUEST, "PATCH")
  c.setopt(c.POSTFIELDS, urllib.urlencode(params))
  c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=args.bill))
  c.setopt(c.WRITEFUNCTION, response.write)
  c.setopt(c.HTTPHEADER, ['Accept: text/json',
                          'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                          auth_header.substitute(auth_encoded=auth_encoded)])    
  c.perform()
  responseCode = c.getinfo(c.HTTP_CODE)
  try:
    message = '\nJSON Response:\n' + str(json.loads(response.getvalue()))
  except ValueError: 
    message = '\nno JSON response'

  if response != 200:
    raise QiwiApiException('HTTP Status: ' + str(responseCode) + message)

  return message

# configure command line arguments
arg_parser = argparse.ArgumentParser()
subparsers = arg_parser.add_subparsers(help='Allowed commands')
create_parser = subparsers.add_parser('create', help=create_bill.__doc__)
create_parser.add_argument('-u', '--user', help='user phone number', required=True)
create_parser.add_argument('-a', '--amount', help='amount of money to pay', required=True)
create_parser.add_argument('-c', '--account', help='user personal account number', required=True)
create_parser.add_argument('-b', '--bill', help='bill unique ID', required=True)
create_parser.set_defaults(func=create_bill)

check_parser = subparsers.add_parser('check', help=check_bill_status.__doc__)
check_parser.add_argument('-b', '--bill', help='bill unique ID', required=True)
check_parser.set_defaults(func=check_bill_status)

reject_parser = subparsers.add_parser('reject', help=reject_bill.__doc__)
reject_parser.add_argument('-b', '--bill', help='bill unique ID', required=True)
reject_parser.set_defaults(func=reject_bill)

# parse command line arguments
command_args = arg_parser.parse_args()

auth = Template('$login:$password')
url = Template('https://w.qiwi.com/api/v2/prv/$provider_id/bills/$bill_id')
auth_encoded = base64.b64encode(auth.substitute(login=auth_parms.get('login'),password=auth_parms.get('password')))
auth_header = Template('Authorization: Basic $auth_encoded')
bill_term = 10 #срок действия счета

# QIWI API exception
class QiwiApiException(Exception):
    pass

print command_args.func(command_args)