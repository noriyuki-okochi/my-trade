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
cmdline = ''
for arg in args:
    cmdline += f"{arg} "
#    
print(cmdline)

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
# connect AUto-trade.db
db = MyDb(DB_PATH)
#
# 取引最小単位（小数点以下桁数）
#  
trade_unit = {\
    'btc':10000,\
    'eth':1,\
    'iost':1,\
    'matic':1\
}
#　デフォルト取引量取得
def get_amount(exchange, symbol, trade, rate):
    symbol = symbol.lower()
    if trade == TRADE_BUY:
        amount = order_amount_jpy/rate
    else:       #TRADE_SELL
        amount = db.get_balanceAmount(exchange, symbol)
    
    # 最小単位以下を切り捨てる
    amount = int( amount * trade_unit[symbol] )
    amount = amount/trade_unit[symbol]
    return amount
#
# debug
#amount = get_amount("gmocoin", "btc", TRADE_BUY,  6635000.0)
#print(f"get_amount = {amount:8,.8f}")
#order = db.get_lastOrder("gmocoin", "BTC", TRADE_BUY)
#print(f"last_order = {order}")
#
# execute trade
#
def exec_trade(exchange, symbol, trade, type, rate, amount=None):
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
        id = 0
    #
    if id == 0:
        return id       # this coin is not supported.
    #
    print(f">exec_trade:rate={rate}, amount={amount}")
    #
    if amount == None or amount == 0.0:
        amount = get_amount(exchange, symbol, trade, rate)
        if amount == None or amount == 0.0:
            return 0
    
    order_jpy = int(amount * rate)
    print(f">{symbol}:{trade} amount={amount:8,.3f}, rate={rate:13.3f}, order_jpy={order_jpy}")

    id = tradeObj.execOrder(symbol, trade, type, rate, amount)
    if id != None:
        id = int(id)
        symbol = symbol.upper()
        rate = float(f"{rate:.3f}")
        amount = float(f"{amount:.4f}")
        db.insert_orders(id, exchange, symbol, trade.upper(), type, rate, amount)
        db.adjust_balance(exchange, symbol, trade.upper(), amount)
    return id
#
# コマンド引数のチェック
#
opts = [opt for opt in args ]
#
if len(opts) > 1 and opts[1] == '-h':
    print(" -tRADE (gmo|coin) <symbol> (buy|sell) <size> [<rate>]")
    print(" -tRADElOG (gmo|coin) <symbol> (buy|sell) <rate>")
    print(" -cANCLE (gmo|coin) <id>")
    print(" -bENEFIT (gmo|coin) <symbol> [<from-date>]:[<to-date>]")
    print(" -uPDATE (trigger|orders) <key-val> <item> [<value>]")
    print(" -dELETE([0-9]+)[y|m|d]")
    print(" -Header [-t]")
    print(" -sKIPUpdateTrigger")
    exit()
#
dontSampling = False
updateTrigger = 3
if len(opts) == 2 and opts[1] == '-s':
    # 自動取引トリガーの更新をスキップする
    updateTrigger = 0

if len(opts) > 1 and opts[1] == '-H':
    # ヘッダ部の表示のみで終了する
    dontSampling = True
    # 自動取引トリガーの更新をスキップする
    updateTrigger = 0
    if len(opts) > 2 and opts[2].startswith('-t'):
        # 自動取引トリガーを更新する
        updateTrigger = 3
        if opts[2] == '-tb':
            updateTrigger = 1
        if opts[2] == '-ts':
            updateTrigger = 2

#
# 現物取引の注文（成行）実行
#    -t (gmo|coin) <symbol> (buy|sell) <size> [<rate>]
#       <symbol>  :: {bit|eth}
#       <size>    :: 9.99999
# 現物取引の注文ログ登録
#    -tl (gmo|coin) <symbol> (buy|sell) <rate>
#       <timestamp>:: Y-m-d H:M:S
##
if len(opts) >= 6 and (opts[1] == '-t' or opts[1] == '-tl'):
    exchange = opts[2]
    symbol = opts[3]
    side = opts[4]
    if opts[1] == '-tl':
        option = 'l'   
        rate = opts[5]
    else:        
        option = 't'
        size = opts[5]
    if exchange in ['coin','gmo']:
        if exchange == 'coin':
            exchange = EXCHANGE_CHECK
        else:
            exchange = EXCHANGE_GMO
        if not symbol in auto_coins:
            illegal = symbol
            exchange = None 
        if not side in ['buy', 'sell']:
            illegal = side
            exchange = None 
        if option == 't' and (not is_float(size)):
            illegal = size
            exchange = None
        #
        if option == 't':
            rate = 0.0
            if len(opts) > 6:
                rate = opts[6]
                if not is_float(rate):
                    illegal = rate
                    exchange = None
        else:
            print(f">Input timeStamp[YYYY-mm-dd HH:MM:SS'].")
            timestamp = input('>>')
            try:
                d = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                illegal = timestamp
                exchange = None
            if not is_float(rate):
                illegal = rate
                exchange = None
    else:
        illegal = exchange
        exchange = None
    #   
    if exchange != None: 
        if option == 't':
            amount = float(size)
            #print(f">request {side}-order of {symbol}({size:8,.3f}) to {exchange}....")
            print(f">Are you sure?[y/n].")
            ans = input('>>')
            if ans == 'y':
                id = exec_trade(exchange, symbol, side, 'MARKET', rate, amount)
                print(f">ID={id}")
                if id != None:
                    # insert to DB(ratelogs)
                    db.insert_ratelogs(exchange, symbol+'_'+side, rate)
        else:
            # insert to DB(ratelogs)
            db.insert_ratelogs(exchange, symbol+'_'+side, rate, timestamp)
    else:
        if option == 't':
            print(f">illegal argument[{illegal}]!!:  -t (gmo|coin) (btc|eth) (buy|sell) <size> ")
        else:
            print(f">illegal argument[{illegal}]!!:  -tl (gmo|coin) (btc|eth) (buy|sell) <rate> ")
    exit()
#
# 現物取引の注文（成行）取り消し
#    -c  (gmo|coin) <id>
#       <id>:: order-id
#
if len(opts) == 4 and opts[1] == '-c':
    exchange = opts[2]
    id = opts[3]
    if exchange in ['coin','gmo']:
        if exchange == 'coin':
            obj = coincheck
        else:
            obj = gmocoin
        #
        if id.isdigit():
            print(f">Are you sure?[y/n].")
            ans = input('>')
            if ans == 'y':
                ret = obj.cancelOrders(id)
                print(f">ret={ret}")
        else:
            print(f">illegal argument[{id}]!!:  -c (gmo|coin) <id>")
    else:
        print(f">illegal argument[{exchange}]!!:  -c (gmo|coin) <id>")
    #
    exit()
#
# 利益集計
#    -b (gmo|coin) <symbol> <period>
#       <period>    :: [<from-date>]:[<to-date>]
#       <date>      :: yyyy-mm-dd
#
if len(opts) > 1 and opts[1] == '-b':
    if len(opts) >= 5:
        value = None
        exchange = opts[2]
        symbol = opts[3]
        period = opts[4]
        if exchange in ['gmo','coin']:
            if exchange == 'gmo':
                exchange = 'gmocoin'
            else:
                exchange = 'coincheck'
            #
            if symbol in ['btc', 'BTC']:
                if period.find(':') != -1:
                    fdate = period[:period.find(':')]
                    tdate = period[period.find(':')+1:]
                    benefit = db.get_benefit(exchange, symbol, fdate, tdate)
                    if benefit != None:
                        print(f">{exchange}:{symbol}:Benefit = {benefit:,}")
                else:
                    print(f">illegal period[{period}]!!")
            else:
                print(f">illegal symbol[{symbol}]!!")
        else:
            print(f">illegal exchange[{exchange}]!!")
    else:
        print(f">arguments is insufficient.!!")
    exit()
#
# テーブルの更新
#    -u  (trigger|orders) <key-val> <item> [<value>]
#       <key-val>   :: key-value(seqnum|id)
#       <item>      :: column-name
#
if len(opts) >= 5 and opts[1] == '-u':
    value = None
    table = opts[2]
    keyVal = opts[3]
    item = opts[4]
    if len(opts) == 6:
        value = opts[5]
    if table in ['trigger','orders', 't', 'o']:
        if table == 't':
            table = 'trigger'
        elif table == 'o':
            table = 'orders'
        #
        item_ok = True
        if table == 'orders' and (not item in ['rate', 'amount']):
            item_ok = False
        if table == 'trigger' and (not item in ['rate', 'method', 'amount', 'count']):
            item_ok = False
        #
        if keyVal.isdigit():
            if item_ok:
                if value == None:
                    print(f">Please input new-value.![/:cancle]")
                    value = input('>')
                if value != '/':
                    ret = db.update_any(table, keyVal, item, value)
                    print(f">ret={ret}")
            else:
                print(f">'{item}' can not specified.!!")
        else:
            print(f">illegal key-val[{keyVal}]!!")
    else:
        print(f">illegal table-name[{table}]!!")
    #
    exit()
#
# check option to delete rate-logs.
#     -d([0-9]+)[y|m|d]
#
opts = [opt[2:] for opt in args if opt.startswith('-d')]
if len(opts) > 0:
    deloptstr = opts[0] 
    if not deloptstr[-1] in ['d','m', 'y']:
        deloptstr += 'y'
    if deloptstr[:len(deloptstr)-1].isnumeric():
        delval = int(deloptstr[:len(deloptstr)-1])
        if delval != None:
            print(f"log-delete option:{deloptstr}")
            last_datetime = last_datetime(delval, deloptstr[-1]) 
            print(f"The last-datetime is {last_datetime}. Are you sure?[y/n].")
            ans = input('>')
            if ans == 'y':
                db.delete_ratelogs(last_datetime)
    else:
        print(f"log-delete option:illegal parameter.")
        print("option: -d{9}...[y(default)|m|d]")
    db.close()
    exit() 
#
print('<< Auto-trade start >>')

if delval != None:
    last_datetime = last_datetime(delval, delopt) 
    db.delete_ratelogs(last_datetime)
    print(f"the rate-logs before {last_datetime} have deleted now.")

#
# 自動取引のトリガー（レート値）登録
#
if updateTrigger != 0:
    print(f"<< tigger >>")
    for sym in auto_coin_symbols:
        print(f" -- {sym} --")
        if target_rate[sym] != None:
            print(f"{sym}:{target_rate[sym]}")
        if buy_rate[sym] != None and (updateTrigger & 1) != 0:
            print(f"{sym}_buy_rate  :{buy_rate[sym]}")
            db.insert_trigger(sym, TRADE_BUY, buy_rate[sym].split())
        if sell_rate[sym] != None and (updateTrigger & 2) != 0:
            print(f"{sym}_sell_rate :{sell_rate[sym]}")
            db.insert_trigger(sym, TRADE_SELL, sell_rate[sym].split())
    print('-')
    print(f"< hist_continuing >  = {hist_continuing}")
    print(f"< order_amount_jpy > = {order_amount_jpy}")
#
# 現在資産残高表示
#
print('\n<< balance >>')
#
# coincheck 現在レート取得
#
URL = 'https://coincheck.com/api/rate/'
coins = ['btc_jpy','eth_jpy','iost_jpy','matic_jpy']
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
# coincheck 残高
#
print('-- coincheck --                                           -- Latest trade(buy) --')
path_balance = '/api/accounts/balance'
names = ['jpy', 'btc','eth','iost','matic']
try:
    result = coincheck.get(path_balance)
except CoinApiError as e:
    print(e)
    exit()
#print(result)
for key, item in result.items():
    if key in names:
        i = names.index(key)
        pre = 0
        jpy = int(float(item)*float(conversionRate[i]))
        pre = db.update_balance(EXCHANGE_CHECK, key, 
                          float(item), 
                          float(conversionRate[i]),
                          jpy
                        )
        pre = jpy - pre
        order = db.get_lastOrder(EXCHANGE_CHECK, key, TRADE_BUY)
        outstring = f"{key:5}:"\
                  + f"{float(item):13,.5f}("\
                  + f"{float(conversionRate[i]):13,.3f}) ="\
                  + f"{jpy:8,}({pre:8,})     {order}"
        if  order != None:
            outstring += f"  ({int(order['rate']*order['amount']):6,})"
        print(outstring)
#
# GMO-coin　資産残高
#
print('-- GMO-coin --                                           -- Latest trade(buy) --')
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
            jpy = int(float(data['amount'])*float(data['conversionRate']))
            pre = db.update_balance(EXCHANGE_GMO, data['symbol'].lower(),
                              float(data['amount']), 
                              float(data['conversionRate']),
                              jpy
                            )
            pre = jpy - pre
            order = db.get_lastOrder(EXCHANGE_GMO, data['symbol'], TRADE_BUY)
            outstring = f"{data['symbol']:5}:"\
                      + f"{float(data['amount']):13,.5f}("\
                      + f"{float(data['conversionRate']):13,.3f}) ="\
                      + f"{jpy:8,}({pre:8,})     {order}"
            if  order != None:
                outstring += f"  ({int(order['rate']*order['amount']):6,})"
            print(outstring)

else:
    print('respons status error!!')
#
# GMO-coin　最新の約定履歴
#
path_latest = '/v1/latestExecutions'
try:
    params = { "symbol": "BTC", "page": 1, "count":100 }
    result = gmocoin.get(path_latest, params)
except CoinApiError as e:
    print(e)
    exit()
if result['status'] == 0:
    #print('respons status ok!!')
    data = result['data']
    #print(f"{result}")
    if any(data):   # len(data) != 0
        lists = data['list']
        order = { 'id': 0, 'size': 0.0, 'price': 0, 'count': 0}
        count = 0
        #print(f"\n")
        for list in lists:
            count += 1
            print(f">latest({count}):{list['orderId']} {list['symbol']:4} {list['side']:4} {list['price']:>9}({list['size']})")
            if order['id'] == list['orderId']:
                order['size'] += float(list['size'])
                order['price'] += int(int(list['price'])*float(list['size']))
                order['count'] += 1
            else:
                if order['id'] != 0:
                    # 同じ注文IDの約定レートの加重平均で更新する
                    rate = order['price']/(order['size'])
                    db.update_orderRate(order['id'], rate)
                #
                order['id'] = list['orderId'] 
                order['size'] = float(list['size']) 
                order['price'] = int(int(list['price'])*float(list['size']))
                order['count'] = 1 
        # 
        if order['id'] != 0:
            # 同じ注文IDの約定レートの加重平均で更新する
            rate = order['price']/(order['size'])
            db.update_orderRate(order['id'], rate)
        #
    else:
        print('>latest execution none')
else:
    print('>respons status error!!')
#
#
if dontSampling:
    # ヘッダ部の表示のみで終了する
    exit(0)
#
#################
#  直近取得レート
#################
last_rate = {'btc':None,
             'eth':None,
             'iost':None,
             'matic':None
            }
#################
# １時間前レート
#################
before_rate = {'btc':None,
             'eth':None,
             'iost':None,
             'matic':None
            }
#
# 起動時初期値
#
last_time = None
for symbol in last_rate:
    rslt = db.select_lastRate(EXCHANGE_CHECK, symbol, RATELOGS_DAYS)
    if rslt == None:
        db.insert_ratelogs(EXCHANGE_CHECK, symbol, 0.0)
        last_rate[symbol] = 0.0    
    else:
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
            'IOST':'iost_jpy',\
            'MATIC':'matic_jpy'\
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
                if b_rate == 0.0:
                    ratio = 0.0
                else:
                    ratio = (rate - before_rate[sym])/before_rate[sym]*100
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
                    if ratio < 0.0 and abs(ratio) > min_ratio[i]:
                        min_ratio[i] = abs(ratio)
                        blink_flg = True
                    if ratio > 0.0 and abs(ratio) > max_ratio[i]:
                        max_ratio[i] = abs(ratio)
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
                    # 「売り」のトリガーチェック
                    rs = db.check_sell_tradeRate(sym, rate, last_rate[sym])
                    if rs != None:
                        tradeSymbol = key
                        exchange = rs['exchange']
                        if rs['exectype'] != 'STOP':
                            trade = TRADE_SELL
                        else:
                            trade = TRADE_BUY
                    else:
                        # 「買い」のトリガーチェック
                        rs = db.check_buy_tradeRate(sym, rate, last_rate[sym])
                        if rs != None:
                            tradeSymbol = key
                            exchange = rs['exchange']
                            if rs['exectype'] != 'STOP':
                                trade = TRADE_BUY
                            else:
                                trade = TRADE_SELL
                        # 警報のトリガーチェック
                        elif db.check_tradeRate(TRADE_SELL, sym, rate, last_rate[sym]) == True:
                            tradeSymbol = key
                            exchange = '*'
                            trade = TRADE_SELL
                        elif db.check_tradeRate(TRADE_BUY, sym, rate, last_rate[sym]) == True:
                            tradeSymbol = key
                            exchange = '*'
                            trade = TRADE_BUY
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
                    #exchange = rs['exchange']
                    #print(f"exchange:{exchange}")
                    alart = 'alart'
                    id = None
                    amount = None
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
                                        rs['exectype'],  
                                        rate,
                                        rs['amount'])
                        if id != 0:
                            title += f"実行（{id}）"
                            alart = 'aouto'
                            amount = rs['amount']
                        else:
                            title += f"実行（手動）"
                            alart = 'manual'
                    #
                    text = f"{tradeSymbol:<4} :"\
                         + f"{last_rate[sym]:13,.3f}　-> {rate:13,.3f}"\
                         + f"（{((rate - last_rate[sym])/last_rate[sym]*100):5,.2f}%）：{amount}"
                    if trade == TRADE_SELL:
                        tradeSymbol = tradeSymbol + '_sell'
                        alert_text = colored_16(STYLE_BLINK,FG_GREEN,BG_BLACK,\
                                        f"<<--- send {alart} mail({trade}:{text})  --->>")
                    else:
                        tradeSymbol = tradeSymbol + '_buy'
                        alert_text = colored_16(STYLE_BLINK,FG_GREEN,BG_BLACK,\
                                        f"<<--- send {alart} mail({trade}:{text})  --->>")
                    print(alert_text + colored_reset())
                    # send gmail
                    send_gmail( to_address=address, subject=title, body=text)
                    if id != None and id != 0:
                        print(f"insert auto-log({id}):{tradeSymbol}({rate})")
                        # insert to DB(ratelogs)
                        db.insert_ratelogs(exchange, tradeSymbol.lower(), rate)
                    #
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
