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
import requests
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
        self.trade_unit = {\
                'btc':10000,\
                'eth':100,\
                'iost':1,\
                'matic':1\
            }

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

    def delete(self, path):
        uri = self.url + path
        nonce = str(int(time.time()))
        message = nonce + uri
        signature = self.getSignature(message)
        return requests.delete(
            uri,
            headers = self.getHeader(self.access_key, nonce, signature)
        ).json()

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
        
    # (requests版)POST
    def requestPost(self, path, params=None):
        uri = self.url + path
        params = json.dumps(params)
        nonce = str(int(time.time()))
        message = nonce + uri + params
        signature = self.getSignature(message)
        headers = self.getHeader(self.access_key, nonce, signature)
        try:
            res = requests.post(uri, headers=headers, data=params, timeout=5)
            if res.status_code == 200:
                res = res.json()
                print(f"requestPost:{res}")
            else:
                print(f"requestPost:status={res.status_code}")
                print(f"requestPost:{res.json()}")
                res = None
        except requests.exceptions.Timeout as e:
            print("Timeout:", e)
            res = None
        except requests.exceptions.RequestException as e:
            print("RequestException:", e)
            res = None
        #print(res)
        return res

    def execOrder(self, symbol, order, extype, rate, amount, path='/api/exchange/orders'):
        if order.lower() == 'buy' and extype.lower() == 'market':
            # 金額に変換
            unit = 1/self.trade_unit[symbol.lower()]
            #amount = int((amount + unit)*rate)
            amount = int((amount)*rate)
            size = f"{amount}"
            print(f"amount={amount/rate:.6f}")
        else:
            if symbol.lower() == 'btc':
                size = f"{amount:.8f}"
            elif symbol.lower() == 'eth':
                size = f"{amount:.6f}"
            elif symbol.lower() == 'iost':
                size = f"{amount:.6f}"
            else:
                return None
        #
        rate = f"{rate:.4f}"
        symbol = symbol.lower() + "_jpy"
        if extype.lower() == "market":
            order = "market_" + order.lower()
        if order == "market_buy":
            reqbody = {
                "pair": symbol,
                "order_type": order,
                "market_buy_amount":size
            }
        else:
            reqbody = {
                "pair": symbol,
                "order_type": order,
                "rate":rate,
                "amount":size
            }
        #
        print(reqbody)
        try:
            result = self.requestPost(path, reqbody)
            if result != None:
                if result['success'] == True:
                    return result['id']
            #print(result)
            return None
        except:
            print('execOrder:exception!!')
            return None
    #
    def cancelOrders(self, ids, path='/api/exchange/orders/'):
        path = path + ids
        res = self.delete(path)
        return res
# eof