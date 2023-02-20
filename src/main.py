#
#main
#     
import sys
#print(sys.path)
import os
#from math import sqrt
import json
import time
from datetime import datetime
#import hmac
#import hashlib
#import traceback
import urllib.request as http
#import urllib.parse as parser
#import pandas as pd
# local
from env import *
from myApi import *
from coincheck.coincheck import *
from gmocoin.gmocoin import GmoCoin
from mysqlite3.mysqlite3 import MyDb

#print(http.__file__)
#
# start of main
#
print(os.getcwd())
# print command line(arguments)
args = sys.argv
cmdline = f"{args[0]}"
if len(args) > 1:
    cmdline += f" {args[1]}"
print(cmdline)

# connect AUto-trade.db
db = MyDb(DB_PATH)

print('<< Auto-trade start >>')
#
# 自動取引のトリガー（レート値）登録
# BTC
if btc_sell_rate != None:
    print(f"btc_sell_rate :{btc_sell_rate}")
    db.insert_trigger(SYM_BTC, TRADE_SELL, btc_sell_rate.split())
if btc_buy_rate != None:
    print(f"btc_buy_rate  :{btc_buy_rate}")
    db.insert_trigger(SYM_BTC, TRADE_BUY, btc_buy_rate.split())
# ETH
if eth_sell_rate != None:
    print(f"eth_sell_rate :{eth_sell_rate}")
    db.insert_trigger(SYM_ETH, TRADE_SELL, eth_sell_rate.split())
if eth_buy_rate != None:
    print(f"eth_buy_rate  :{eth_buy_rate}")
    db.insert_trigger(SYM_ETH, TRADE_BUY, eth_buy_rate.split())
# OMG
if omg_sell_rate != None:
    print(f"omg_sell_rate :{omg_sell_rate}")
    db.insert_trigger(SYM_OMG, TRADE_SELL, omg_sell_rate.split())
if omg_buy_rate != None:
    print(f"omg_buy_rate  :{omg_buy_rate}")
    db.insert_trigger(SYM_OMG, TRADE_BUY, omg_buy_rate.split())
# IOST
if iost_sell_rate != None:
    print(f"iost_sell_rate:{iost_sell_rate}")
    db.insert_trigger(SYM_IOST, TRADE_SELL, iost_sell_rate.split())
if iost_buy_rate != None:
    print(f"iost_buy_rate :{iost_buy_rate}")
    db.insert_trigger(SYM_IOST, TRADE_BUY, iost_buy_rate.split())
#
# create instance for CoinCheck private-API
#
access_key = ACCESS_KEY_CHECK
secret_key = SECRET_KEY_CHECK
coincheck = Coincheck(access_key, secret_key)
#
# create instance for GMO-Coin private-API
#
access_key = ACCESS_KEY_GMO
secret_key = SECRET_KEY_GMO
gmocoin = GmoCoin(access_key, secret_key)
#
################
# 現在資産残高表示
################
print('\n<< balance >>')
#
#coincheck 現在レート取得
#
print('-- coincheck --')
URL = 'https://coincheck.com/api/rate/'
coins = ['btc_jpy','eth_jpy','omg_jpy','iost_jpy']
conversionRate=[]
conversionRate.append(float(1))
for coin in coins:
    req = http.Request(URL+coin, method='GET')
    res = http.urlopen(req)
    if res.status == 200:
        body = res.read()
        result = json.loads(body.decode())
        conversionRate.append(float(result['rate']))
        res.close()
    else:
        print(f"{coin:4}:error!![status = {result['status']}]")
#print(conversionRate)
#
#coincheck 残高
#
path_balance = '/api/accounts/balance'
names = ['jpy', 'btc','eth','omg','iost']
try:
    result = coincheck.get(path_balance)
except CoinApiError as e:
    print(e)
    exit()
#print(result)
for key, item in result.items():
    if key in names:
        i = names.index(key)
        outstring = f"{key:4}:"\
                  + f"{float(item):13,.5f}("\
                  + f"{float(conversionRate[i]):13,.3f}) ="\
                  + f"{int(float(item)*float(conversionRate[i])):13,}"
        print(outstring)
        db.update_balance(EXCHANGE_CHECK, key, 
                          float(item), 
                          float(conversionRate[i]))
#
#GMO-coin　資産残高
#
print('-- GMO-coin --')
path_balance = '/v1/account/assets'
try:
    result = gmocoin.get(path_balance)
except CoinApiError as e:
    print(e)
    exit()
if result['status'] == 0:
    datalist = result['data']
    for data in datalist:
        if float(data['amount']) > 0.0:
            outstring = f"{data['symbol']:4}:"\
                      + f"{float(data['amount']):13,.5f}("\
                      + f"{float(data['conversionRate']):13,.3f}) ="\
                      + f"{int(float(data['amount'])*float(data['conversionRate'])):13,}"
            print(outstring)
            db.update_balance(EXCHANGE_GMO, data['symbol'].lower(),
                              float(data['amount']), 
                              float(data['conversionRate']))

else:
    print('respons status error!!')

#################
#  直近取得レート
#################
last_rate = {'btc':None,
             'eth':None,
             'omg':None,
             'iost':None
            }
#################
# １時間前レート
#################
before_rate = {'btc':None,
             'eth':None,
             'omg':None,
             'iost':None
            }
#
# 起動時初期値
#
last_time = None
for symbol in last_rate:
    #last_rate[symbol],last_time = db.select_lastRate(EXCHANGE_CHECK, symbol, RATELOGS_DAYS)
    rslt = db.select_lastRate(EXCHANGE_CHECK, symbol, RATELOGS_DAYS)
    #print(rslt)
    last_rate[symbol] = rslt[0]    
    before_rate[symbol] = last_rate[symbol]
last_epoch = rslt[1]
#
print('\n<<--- most recent registerd coinCheck-rate --->>')
last_time = datetime.fromtimestamp(last_epoch)
print(f"{last_rate}       ({last_time.strftime('%Y-%m-%d %H:%M:%S'):^22})")
#
#################
# interval 
#################
print(f"\n<<--- coinCheck-rate every {INTERVAL} seconds for {SLEEP_DAYS} days --->>")

symbols = {\
            'BTC':'btc_jpy',\
            'ETH':'eth_jpy',\
            'OMG':'omg_jpy',\
            'IOST':'iost_jpy'\
}
# edit header line and display first.
header =''
for key, item in symbols.items():
    symbol = '--' + key + '--'
    header = header + f"{symbol:^22}"

print(header+f"({time_stamp():^22})")
#
#signal function
#
counter = MAX_LINES
ud_cont = [0 for key in symbols]
ud_rate = [0.0 for key in symbols]
max_ratio = [0.0 for key in symbols]
min_ratio = [0.0 for key in symbols]
#
# execute trade
#
def exec_trade(exchange, symbol, trade, type, rate):
    id = None
    if exchange == EXCHANGE_CHECK:
        tradeObj = coincheck
        if symbol.upper() not in ['BTC','ETH']:
            id = 0
    elif exchange == EXCHANGE_GMO:
        tradeObj = gmocoin
        if symbol.upper() not in ['BTC','ETH']:
            id = 0
    else:
        return None
    #
    if id == 0:
        return id       # this coin is not supported.
    #
    amount = order_amount_jpy/int(rate)
    print(f"order_amount_jpy = {order_amount_jpy}")
    print(f"{symbol}:{trade} amount = {amount}")
    id = tradeObj.execOrder(symbol, trade, type, rate, amount)
    if id != None:
        symbol = symbol.upper() + '_JPY'
        rate = float(f"{rate:.3f}")
        amount = float(f"{amount:.4f}")
        db.insert_orders(id, exchange, symbol, trade.upper(), type, rate, amount)
    return id
#
# execute the following ticker function every INTERVAL 
#  
def ticker(arg1, arg2):
    global counter
    global ud_cont
    global ud_rate

    address = 'noriyuki_okochi@ybb.ne.jp'
    counter -= 1
    rateString = ''
    try:
        # display header    
        if counter == 0:
            print(header+f"({time_stamp():^24})")
            counter = MAX_LINES
            #print(ud_cont)
        #
        # edit a line of rate
        #
        i = 0
        for key, item in symbols.items():
            # get current rate(_jpy) from coincheck
            req = http.Request(URL+item, method='GET')
            res = http.urlopen(req)
            if res.status == 200:
                body = res.read()
                result = json.loads(body.decode())
                rate = float(result['rate'])
                sym = key.lower()
                rateString = rateString + f"{rate:> 13,.3f}"
                title = None
                if ud_rate[i] == 0.0:
                    ud_rate[i] = rate
                b_rate = before_rate[sym]
                ratio = (rate - before_rate[sym])/before_rate[sym]*100
                #b_ratio = (rate - last_rate[sym])/last_rate[sym]*100
                blink_flg = False
                if counter == MAX_LINES:    # per an hour
                    before_rate[sym] = rate
                    min_ratio[i] = 0.0
                    max_ratio[i] = 0.0
                    if ratio < 0.0 :    # down
                        if ud_cont[i] > 0:
                            ud_cont[i] = 0
                            ud_rate[i] = rate
                        ud_cont[i] -= 1
                    else:               # up
                        if ud_cont[i] < 0:
                            ud_cont[i] = 0
                            ud_rate[i] = rate
                        ud_cont[i] += 1
                    if abs(ud_cont[i]) >= 3:
                        #3回以上の連続の上昇・下落は初回レートと比較
                        ratio = (rate - ud_rate[i])/ud_rate[i]*100
                        b_rate = ud_rate[i]
                    if abs(ratio) >= blink_rate:
                        blink_flg = True
                else:
                    if ratio < 0.0 and ratio < min_ratio[i]:
                        min_ratio[i] = ratio
                        #blink_flg = True
                    if ratio > 0.0 and ratio > max_ratio[i]:
                        max_ratio[i] = ratio
                        blink_flg = True
                #
                if abs(ratio) >= blink_rate and blink_flg == True:
                    if ratio < 0.0:     # down(Red,Blink)
                        ratioString = colored_16(STYLE_BLINK,FG_RED,BG_BLACK,f"({abs(ratio):4.2f}%)")
                        title =f"アラート通知（{key}の下落）"
                    else:               # up(Blue,Blink)
                        ratioString = colored_16(STYLE_BLINK,FG_BLUE,BG_BLACK,f"({ratio:4.2f}%)")
                        title =f"アラート通知（{key}の上昇）"
                    if counter == MAX_LINES and abs(ud_cont[i]) >= 3:
                        title += f"：{abs(ud_cont[i])}回連続"
                        #print(ud_rate)
                else:               
                    if ratio < 0.0:     # down(Red)
                        ratioString = colored_16(STYLE_NON,FG_RED,BG_BLACK,f"({abs(ratio):4.2f}%)")
                    else:               # up(Blue)
                        ratioString = colored_16(STYLE_NON,FG_BLUE,BG_BLACK,f"({ratio:4.2f}%)")
                #
                if counter == MAX_LINES:    # per an hour
                    ratioString += (colored_reset() + f"{abs(ud_cont[i]):2}")
                else:                       # per four minuts
                    ratioString += "  "
                rateString += ratioString + colored_reset()
                #
                # send gmail
                #
                if title != None:
                    text = f"{key:<4} :"\
                             + f"{b_rate:13,.3f}　-> {rate:13,.3f}"\
                             + f"（{abs(ratio):5,.2f}%）"
                    #print(text)
                    send_gmail( to_address=address, subject=title, body=text)
                #
                #
                # insert to DB(ratelogs)
                #
                db.insert_ratelogs(EXCHANGE_CHECK, sym, rate)
                #
                if last_rate[sym] != None:
                    if db.check_tradeRate(TRADE_SELL, sym, rate, last_rate[sym]) == True:
                        tradeSymbol = key
                        if db.execType() != 'STOP':
                            trade = TRADE_SELL
                        else:
                            trade = TRADE_BUY
                    elif db.check_tradeRate(TRADE_BUY, sym, rate, last_rate[sym]) == True:
                        tradeSymbol = key
                        if db.execType() != 'STOP':
                            trade = TRADE_BUY
                        else:
                            trade = TRADE_SELL
                    else:
                        tradeSymbol = None
                        trade = None
                if tradeSymbol != None:
                    # send gmail or execute auto-trade
                    if trade == TRADE_SELL:
                        title =f"自動取引（{tradeSymbol}の売り）"
                    else:
                        title =f"自動取引（{tradeSymbol}の買い）"
                    #
                    exchange = db.toExchange()
                    #print(f"exchange:{exchange}")
                    if exchange == None:
                        title += "通知"
                    elif exchange == '*':
                        title += "警報"
                    else:
                        # 
                        # execute auto-trade
                        #
                        id = exec_trade(exchange, 
                                        tradeSymbol, 
                                        trade,
                                        db.execType(),  
                                        rate)
                        if id != 0:
                            title += f"実行（{id}）"
                        else:
                            title += f"実行（手動）"
                    #
                    text = f"{tradeSymbol:<4} :"\
                         + f"{last_rate[sym]:13,.3f}　-> {rate:13,.3f}"\
                         + f"（{((rate - last_rate[sym])/last_rate[sym]*100):5,.2f}%）"
                    if trade == TRADE_SELL:
                        alert_text = colored_16(STYLE_BLINK,FG_BLUE,BG_BLACK,f"<<--- send alart mail({trade}:{text})  --->>")
                    else:
                        alert_text = colored_16(STYLE_BLINK,FG_RED,BG_BLACK,f"<<--- send alart mail({trade}:{text})  --->>")
                    print(alert_text + colored_reset())
                    # send gmail
                    send_gmail( to_address=address, subject=title, body=text)
                    tradeSymbol = None
                #
                last_rate[sym] = rate
                res.close()
            else:
                print(f"{key:4}:error!![status = {result['status']}]")
            # next symbole
            i += 1
        #
        # display a line of rate
        #
        print(rateString)
    except KeyboardInterrupt:
        db.close()
        exit(0)
#
import signal
signal.signal(signal.SIGALRM, ticker)
signal.setitimer(signal.ITIMER_REAL, 1, INTERVAL)

time.sleep(sleep_time)
print(f"ticker has finished with time-up.(SLEEP_DAYS={SLEEP_DAYS})")

'''
print('-- GMO-coinc --')
URL = 'https://api.coin.z.com/public/v1/ticker?symbol='
symbols = {'BTC':'BTC_JPY','ETH':'ETH_JPY','OMG':'OMG_JPY'}
symbols = {'BTC':''}
symbols = {'BTC':'BTC_JPY','ETH':'ETH_JPY'}
for key, item in symbols.items():
    req = http.Request(URL+item, method='GET')
    res = http.urlopen(req)
    if res.status == 200:
        body = res.read()
        result = json.loads(body.decode())
        print(f"{key:4}:{int(float(result['data'][0]['bid'])):12,}")
        print(f"{key:4}:{int(float(result['rate'])):12,}")
        print(result)
    else:
        print(f"{key:4}:error!![status = {result['status']}]")
'''
'''
#######################
# Create webSocket
#######################
import websocket
#
# define event-handler
#
def on_open(ws):
    message = {
        "command": "subscribe",
        "channel": "ticker",
        "symbol": "BTC"
    }
    print('WS: connected')
    ws.send(json.dumps(message))

def on_message(ws, message):
    print(message)
def on_error(ws, error):
    print(error)
def on_close(ws, status, message):
    print(f"WS: disconnected({status})")

websocket.enableTrace(False)
ws = websocket.WebSocketApp('wss://api.coin.z.com/ws/public/v1',
        on_open = on_open,
        on_message = on_message,
        on_error = on_error,
        on_close = on_close)

try:
    ws.run_forever()
except KeyboardInterrupt:
    ws.close()
'''
'''
        # display  all orders transactions on coinchek
        path_transactions = '/api/exchange/orders/transactions'
        try:
            result = coincheck.get(path_transactions)
        except CoinApiError as e:
            print(e)
            exit()
        print(result)
        # display active orders of OMG on GMOcoin
        path_activeorders = '/v1/activeOrders'
        params = {
            "symbol": "BTC",
            "page":1,
            "count":1
        }
        try:
            result = gmocoin.get(path_activeorders,params)
        except CoinApiError as e:
            print(e)
            exit()
        print(result)
'''
