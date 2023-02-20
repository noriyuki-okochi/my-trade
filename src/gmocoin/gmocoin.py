#
#
#mClass for GMO coin
#     
from distutils.command import install_headers
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
#
# Exception Class for API
#
class CoinApiError(Exception):
    pass
#
# Private API Class for GMO-Coin
#
class GmoCoin:
    def __init__(self,access_key, secret_key, url='https://api.coin.z.com/private'):
        self.access_key = access_key
        self.secret_key = secret_key
        self.url = url

    def get(self, path, params=None):
        uri = self.url + path
        strJson = ''
        if params != None:
            uri = f'{uri}?{parser.urlencode(params)}'

        nonce = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        message = nonce + 'GET' + path
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
        nonce = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        message = nonce + 'POST' + path + params
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
        '''
        return requests.get(
            uri,
            data = params,
            headers = self.getHeader(self.access_key, nonce, signature)
        ).json()
        '''

    def getSignature(self, message):
        signature = hmac.new(
            bytes(self.secret_key.encode('ascii')),
            bytes(message.encode('ascii')),
            hashlib.sha256
        ).hexdigest()
        return signature

    def getHeader(self, access_key, nonce, signature):
        headers = {
            'API-KEY': access_key,
            'API-TIMESTAMP': nonce,
            'API-SIGN': signature,
            'Content-Type': 'application/json'
        }
        return headers
    
    def execOrder(self, symbol, order, type, rate, amount, path='/v1/order'):
        if symbol.upper() == 'BTC':
            size = f"{amount:.4f}"
        elif symbol.upper() == 'ETH':
            size = f"{amount:.2f}"
        else:
            return None
        order = order.upper()
        price = f"{int(rate)}"
        symbol = symbol.upper() + "_JPY"
        reqbody = {
            "symbol": symbol,
            "side": order,
            "executionType":type,
            "price":price,
            "size":size
        }
        print(reqbody)
        try:
            result = self.post(path, reqbody)
            #result = {"status":0, "data":12346}
            if result['status'] == 0:
                return result['data']
            else:
                return None
        except:
            return None

    def cancelOrders(self, ids, path='/v1/cancelOrders'):
        reqbody = {
            "orderIds": ids
        }
        return self.post(path, reqbody)

#eof
