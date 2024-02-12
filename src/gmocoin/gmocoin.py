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
import urllib.error
import urllib.request as http
import urllib.parse as parser
import requests
#print(http.__file__)
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

    # (urllib版)GET
    def get(self, path, params=None):
        uri = self.url + path
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

    # (urllib版)POST
    def post(self, path, params=None):
        uri = self.url + path
        data = parser.urlencode(params).encode()
        params = json.dumps(params)
        nonce = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        message = nonce + 'POST' + path + params
        signature = self.getSignature(message)
        headers = self.getHeader(self.access_key, nonce, signature)
        req = http.Request(uri, data, headers=headers, method='POST')
        try:
            res = http.urlopen(req)
            if res.status == 200:
                body = res.read()
                result = json.loads(body.decode())
            else:
                print(res.msg+' :',res.status)
                raise CoinApiError(f'https status={res.status}')
        except urllib.error.HTTPError as err:
            print('post:HTTP exception!!')
            print(err.code)
            raise CoinApiError(f'HTTPError')
        except urllib.error.URLError as err:
            print('post:URL exception!!')
            print(err.reason)
            raise CoinApiError(f'URLError')
        finally:
            res.close()
        return result 
    
    # (requests版)POST
    def requestPost(self, path, params=None):
        uri = self.url + path
        params = json.dumps(params)
        nonce = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        message = nonce + 'POST' + path + params
        signature = self.getSignature(message)
        headers = self.getHeader(self.access_key, nonce, signature)
        try:
            res = requests.post(uri, headers=headers, data=params, timeout=5)
            if res.status_code == 200:
                res = res.json()
            else:
                res = None
        except requests.exceptions.Timeout as e:
            print("Timeout:", e)
            res = None
        except requests.exceptions.RequestException as e:
            print("RequestException:", e)
            res = None
        return res
    

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
        #symbol = symbol.upper() + "_JPY"   # 信用取引
        symbol = symbol.upper()             # 現物取引
        reqbody = {
            "symbol": symbol,
            "side": order,
            "executionType":type,
            #"price":price,                 # type='LIMIT'時のみ必要、'MARKET'では5103のエラー発生
            "size":size
        }
        print(reqbody)
        try:
            result = self.requestPost(path, reqbody)
            #result = self.post(path, reqbody)
            if result['status'] == 0:
                return result['data']
            else:
                print(result)
                return None
        except:
            print('execOrder:exception!!')
            return None

    def cancelOrders(self, ids, path='/v1/cancelOrders'):
        reqbody = {
            "orderIds": ids
        }
        return self.post(path, reqbody)
#
#eof
