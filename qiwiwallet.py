# -*- coding: utf-8 -*-
from string import Template 
import pycurl
import argparse
import base64
import cx_Oracle
import os
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
#    'password':  '',
#    'logfile': 'qiwi_wallet.log'
#}

#setting up logging
logging.basicConfig(filename=auth_parms.get('logfile'),format = u'%(levelname)-8s [%(asctime)s]  %(message)s',level=logging.DEBUG)

#defining API functions wrappers

def api_create (user, bill, amount, account):
  response = BytesIO()
  params = {'user': 'tel:+' + str(user),
            'amount': amount,
            'ccy': 'RUB',
                'comment': 'bill ' + str(bill) + ' created by billing system',
                  'lifetime': (datetime.datetime.now() + datetime.timedelta(days=10)).replace(microsecond=0).isoformat(),
                  'prv_name': 'STEL',
                  'pay_source': 'qw',
                  'account': account}              
  c = pycurl.Curl()
  c.setopt(c.CUSTOMREQUEST, "PUT")
  c.setopt(c.POSTFIELDS, urllib.urlencode(params))
  c.setopt(c.URL, url.substitute(provider_id=auth_parms.get('provider_id'),bill_id=bill))
  c.setopt(c.WRITEFUNCTION, response.write)
  c.setopt(c.HTTPHEADER, ['Accept: text/json',
                                 'Content-Type: application/x-www-form-urlencoded; charset=utf-8',
                                 auth_header.substitute(auth_encoded=auth_encoded)])    
  c.perform()
  HttpResponseCode = c.getinfo(c.HTTP_CODE)
    
  try:
    message = 'JSON Response: ' + str(json.loads(response.getvalue()))
  except ValueError: 
    message = 'no JSON response'
    
  log_entry = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': HTTP Status: ' + str(HttpResponseCode) + ' '+ message
  if HttpResponseCode != 200:
    logging.error(log_entry)
    return message

  logging.info(log_entry)
  return message

def create_bill (args):
    "creates bills for defined user phones and sum, with specified comment and ID"
    logging.info('args.user_notice=' + str(args.user_notice) + '   args.user_mobile=' + str(args.user_mobile))

    if (args.user_notice != ""):
      logging.info('processing notice phone numbers: \"' + str(args.user_notice) + '\"')
      tel_string = args.user_notice
    elif (args.user_mobile != ""):
      logging.info('processing mobile phone numbers: \"' + str(args.user_mobile) + '\"')
      tel_string = args.user_mobile
    else: 
      message = 'No valid phone numbers entered!'
      logging.error(message)
      return message

    # Делим строку на номера
    phone_numbers = tel_string.split(",")
    for user_phone_number in phone_numbers:
      log_entry = 'processing phone number: \"' + str(user_phone_number) + '\"'
      logging.info(log_entry)
      api_create(user=user_phone_number, amount=args.amount, account=args.account, bill=(str(user_phone_number)+'_'+args.bill))

    return 

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
    HttpResponseCode = c.getinfo(c.HTTP_CODE)
    try:
      message = 'JSON Response: ' + str(json.loads(response.getvalue()))
    except ValueError: 
      message = 'no JSON response'

    log_entry = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': HTTP Status: ' + str(HttpResponseCode) + ' '+ message
    if HttpResponseCode != 200:
      logging.error(log_entry)
      raise QiwiApiException('HTTP Status: ' + str(HttpResponseCode) + '\n' +  message)

    logging.info(log_entry)
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
  HttpResponseCode = c.getinfo(c.HTTP_CODE)
  try:
    message = 'JSON Response: ' + str(json.loads(response.getvalue()))
  except ValueError: 
    message = 'no JSON response'

  log_entry = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ': HTTP Status: ' + str(HttpResponseCode) + ' '+ message  
  if HttpResponseCode != 200:
    logging.error(log_entry)
    raise QiwiApiException('HTTP Status: ' + str(HttpResponseCode) + '\n' + message)

  logging.info(log_entry)
  return message

# configure command line arguments
arg_parser = argparse.ArgumentParser()
subparsers = arg_parser.add_subparsers(help='Allowed commands')

create_parser = subparsers.add_parser('create', help=create_bill.__doc__)
create_parser.add_argument('-m', '--user_mobile', help='user mobile phone number')
create_parser.add_argument('-n', '--user_notice', help='user notice phone number')
create_parser.add_argument('-a', '--amount', help='amount of money to pay', required=True)
create_parser.add_argument('-c', '--account', help='user personal account number', required=True)
create_parser.add_argument('-b', '--bill', help='bill unique ID')
create_parser.set_defaults(func=create_bill, bill=datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

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

# QIWI API exception
class QiwiApiException(Exception):
    pass

if __name__ == "__main__":
  command_args.func(command_args)