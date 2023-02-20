#
#
#Class for coincheck
#     
import sys
#print(sys.path)
import os
from math import sqrt
import json
import time
from datetime import datetime
import hmac
import hashlib
import urllib.request as http
import urllib.parse as parser
#print(http.__file__)
#import requests
#
# Exception Class for API
#
class CoinApiError(Exception):
    pass
#
# Private API Class for Coin-Check
#
class Coincheck:
    def __init__(self,access_key, secret_key, url='https://coincheck.com'):
        self.access_key = access_key
        self.secret_key = secret_key
        self.url = url

    def get(self, path, params=None):
        uri = self.url + path
        strJson = ''
        if params != None:
            uri = f'{uri}?{parser.urlencode(params)}'
            strJson = json.dumps(params)

        nonce = str(int(time.time()))
        message = nonce + uri + strJson
        signature = self.getSignature(message)
        headers = self.getHeader(self.access_key, nonce, signature)
        req = http.Request(uri, headers=headers, method='GET')
        try:
            res = http.urlopen(req)
            if res.status == 200:
                body = res.read()
                result = json.loads(body.decode())
            else:
                print(res.msg+' :',res.status)
                raise CoinApiError(f'https status={res.status}')
        except:
            print('exception!!')
            raise CoinApiError(f'exception')
        #else:
        #    print(res.msg+' :',res.status)
        finally:
            res.close()
        return result 

    def post(self, path, params=None):
        uri = self.url + path
        params = json.dumps(params)
        nonce = str(int(time.time()))
        message = nonce + uri + params
        signature = self.getSignature(message)
        headers = self.getHeader(self.access_key, nonce, signature)
        req = http.Request(uri, params, headers=headers, method='POST')
        try:
            res = http.urlopen(req)
            if res.status == 200:
                body = res.read()
                result = json.loads(body.decode())
            else:
                print(res.msg+' :',res.status)
                raise CoinApiError(f'https status={res.status}')
        except:
            print('exception!!')
            raise CoinApiError(f'exception')
        finally:
            res.close()
        return result 

#    def delete(self, path):
#        uri = self.url + path
#        nonce = str(int(time.time()))
#        message = nonce + uri
#        signature = self.getSignature(message)
#        return requests.delete(
#            uri,
#            headers = self.getHeader(self.access_key, nonce, signature)
#        ).json()

    def getSignature(self, message):
        signature = hmac.new(
            bytes(self.secret_key.encode('ascii')),
            bytes(message.encode('ascii')),
            hashlib.sha256
        ).hexdigest()
        return signature

    def getHeader(self, access_key, nonce, signature):
        headers = {
            'ACCESS-KEY': access_key,
            'ACCESS-NONCE': nonce,
            'ACCESS-SIGNATURE': signature,
            'Content-Type': 'application/json'
        }
        return headers

# eof