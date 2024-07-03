#
#
# Class for sqlite3
#     
import sqlite3
import pandas
import time
from datetime import datetime
from env import *
from myApi import *
#
# Private API Class for sqlite3
#
class MyDb:
    def __init__(self, dbpath='../Auto-trade.db'):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def execute(self, sql):
        return self.cur.execute(sql)
#
# insert or update balance-table
#
    def update_balance(self, exchange, symbol, amount, rate, jpy):
        pre = jpy
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"
        rs = self.cur.execute(sql).fetchone()
        if rs == None:
            sql = "insert into balance(exchange,symbol,amount,rate,jpy) values("\
                + f"'{exchange}',"\
                + f"'{symbol}',"\
                + f"{amount},"\
                + f"{rate},"\
                + f"{jpy})"
            self.cur.execute(sql)
        else:
            pre = rs['jpy']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update balance set "\
                + f"amount={amount},rate={rate},"\
                + f"updated_at='{timestamp}'"\
                + f" where exchange='{exchange}' and symbol='{symbol}'"
            self.cur.execute(sql)
        self.conn.commit()
        return int(pre)
#
# select amount from balance-table
#
    def get_balanceAmount(self, exchange, symbol):
        amount = None
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"

        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            amount = rs['amount']

        print(f">get_balanceAmount=>amount={amount}:sql={sql}")
        return amount
#
# adjust amount 
#  
    def adjust_balance(self, exchange, symbol, trade, amount):
        c_amount = self.get_balanceAmount(exchange, symbol)
        if c_amount != None:
            if trade == 'SELL':
                c_cmount -= amount
            else:     # 'BUY'
                c_cmount += amount
            sql = "update balance set amount = {c_amount} where "\
                + f"exchange='{exchange}' and symbol='{symbol}'"
            self.cur.execute(sql)
            self.conn.commit()
        return c_amount
#
# insert samplling rates logs.
#
    def insert_ratelogs(self, exchange, symbol, rate, timestamp=None):
        if timestamp == None:
            d = datetime.now()
            timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        else:
            d = datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        sql = "insert into ratelogs"\
            + "(exchange,symbol,rate,inserted_at,time_epoch) values("\
            + f"'{exchange}',"\
            + f"'{symbol}',"\
            + f"{rate},"\
            + f"'{timestamp}',"\
            + f"{time_epoc})"
        self.cur.execute(sql)
        self.conn.commit()
#
# insert auto-orders log
#
    def insert_orders(self, id, exchange, pair, trade, type, rate, amount):
        # insert new datas
        sql = "insert into orders(id, exchange, pair, order_side, order_type, rate, amount)"
        sql += f" values({id},'{exchange}','{pair}','{trade}','{type}',{rate},{amount})"
        #print(sql)
        self.cur.execute(sql)
        #
        self.conn.commit()
#
# select the max rate from recent buy-orders-log
#
    def get_maxOrderBuyRate(self, exchange, pair):
        result = None
        # select last sell-record
        sql = "select id from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'SELL' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            id  = rs['id']
            sql = "select max(rate) as max_rate from orders where "
            sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'BUY' "
            sql += f" and id > {id}"
            #print(sql)
            self.cur.execute(sql)
            rs = self.cur.execute(sql).fetchone()
            if rs != None:
                result = rs['max_rate']
        return result
#
# select the min rate from recent sell-orders-log
#
    def get_minOrderSellRate(self, exchange, pair):
        result = None
        # select last buy-record
        sql = "select id from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'BUY' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            id  = rs['id']
            sql = "select min(rate) as min_rate from orders where "
            sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'SELL' "
            sql += f" and id > {id}"
            #print(sql)
            self.cur.execute(sql)
            rs = self.cur.execute(sql).fetchone()
            if rs != None:
                result = rs['min_rate']
        return result
#
# select the last order from orders-log
#
    def get_lastOrder(self, exchange, pair, trade):
        result = None
        # select last record
        sql = "select * from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = '{trade.upper()}' "
        sql += f" order by created_at desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            result = {'rate': rs['rate'], 'amount':rs['amount']}
        return result
#
# 指定期間の利益を集計する
#
    def get_benefit(self, exchange, pair, fdate, tdate):
        benefit = None
        pair = pair.upper() 
        # BUY
        sql = "select sum(rate*amount) as JPY, sum(amount) as AMT, avg(rate) as RATE,"\
              " count(*) as CNT from orders where order_side = 'BUY'"\
             f" and exchange = '{exchange}' and pair = '{pair}'"
        if fdate != '' and tdate != '':
            period = f" and (created_at > '{fdate}' and created_at < '{tdate}')"
        elif tdate == '':
            period = f" and (created_at >= '{fdate}')"
        elif fdate == '':
            period = f" and (created_at < '{tdate}')"
        sql += period
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            jpy = rs['JPY']
            benefit = int(jpy)
            amt = rs['AMT']
            rate = benefit/amt
            count = rs['CNT']
            print(f">Buy ={benefit:,}({amt:.4f} x {rate:.3f}) <{count}>")
            # SELL
            sql = "select sum(rate*amount) as JPY, sum(amount) as AMT, avg(rate) as RATE,"\
                  " count(*) as CNT from orders where order_side = 'SELL'"\
                 f" and exchange = '{exchange}' and pair = '{pair}'"
            sql += period
            self.cur.execute(sql)
            rs = self.cur.execute(sql).fetchone()
            if rs != None:
                jpy = rs['JPY']
                jpy = int(jpy)
                amt = rs['AMT']
                rate = jpy/amt
                count = rs['CNT']
                print(f">SELL={jpy:,}({amt:.4f} x {rate:.3f}) <{count}>")
                #
                print(f">BeneFit={(jpy - benefit):,}({((jpy - benefit)*100/benefit):.2f}%)")
                # 利益
                benefit = jpy - benefit
        return benefit
#
# update the order-rate of orders-log
#
    def update_orderRate(self, order_id,  rate):
        #print(f"update_orderRate:{order_id}({rate:9,.3f})")
        sql = f"update orders set rate={rate} where id={order_id}"
        self.cur.execute(sql)
        self.conn.commit()
#
# update the trigger/orders-table
#
    def update_any(self, table, keyVal, item, value):
        #
        if table == 'trigger':
            prmKey = 'seqnum'
        else:       # 'orders'
            prmKey = 'id'
        #
        sql = f"update {table} set {item}={value} where {prmKey}={keyVal}"
        print(f"update_any:{sql}")
        ret = None
        if value != '-':
            ret = self.cur.execute(sql)
            self.conn.commit()
        #
        return ret
#
# insert trigger info. for auto-trade
#   trigger :: '<target-rate>!<scenario>:<exchange-office>:<amount>'
#  
    def insert_trigger(self, symbol, trade, ratelist):
        # delete old datas
        sql = "delete from trigger where "\
            + f"symbol='{symbol}' and trade='{trade}'"
        self.cur.execute(sql)
        # insert new datas
        for rate in ratelist:
            if rate[0] == '-' or rate[0].isdigit() == True:
                exchange = None
                amount = None
                method = None
                sql = "insert into trigger(symbol,trade,rate,exectype,exchange"
                if rate.find(':') != -1:
                    exchange = rate[rate.find(':')+1:]
                    rate = rate[:rate.find(':')]
                    if rate.find('!') != -1:
                        method = rate[rate.find('!')+1:]
                        rate = rate[:rate.find('!')]
                    if exchange.find(':') != -1:
                        amount = exchange[exchange.find(':')+1:]
                        exchange = exchange[:exchange.find(':')]
                        sql += ",amount"
                    if method != None:
                        sql += ",method"
                else:
                    exchange = '*'
                sql += ")"
                #
                '''
                if rate[0] == '-':
                    exectype = 'STOP'
                    rate = rate[1:]
                else:
                    exectype = 'MARKET'
                '''
                exectype = 'MARKET'
                #
                sql += f" values('{symbol}','{trade}',{rate},'{exectype}','{exchange}'"
                if amount != None:
                    sql += f",'{amount}'"
                    if method != None:
                        sql += f",'{method}'"
                sql += ")"
                #print(f"trigger:{sql}")
                self.cur.execute(sql)
        #
        self.conn.commit()
#
# 最終ログのレートを取得する
#
    def select_lastRate(self, exchange, symbol, logsdays=None):
        sql = "select rate, time_epoch from ratelogs where "\
            + f"exchange='{exchange}' and symbol='{symbol}' "\
            + " ORDER BY time_epoch DESC"
        #print(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs == None:
            return None
        if logsdays != None:
            last_epoch = rs['time_epoch']
            last_epoch -= (3600*24)*logsdays
            sql = "delete from ratelogs where "\
                + f"exchange='{exchange}' and symbol='{symbol}' "\
                + f"and time_epoch < {last_epoch}"
            self.cur.execute(sql)
        return [rs['rate'],rs['time_epoch']]
#
#  トリガー指定のレートを横断したか判定する
#      
    def check_tradeRate(self, trade, symbol, c_rate, l_rate):
        ret = False
        sql = "select * from trigger where "\
            + f"trade='{trade}' and symbol='{symbol}' and "\
            + f"method='IM' and "
            #+ f"count=0 and method='IM' and "
        if trade == 'sell':
            if c_rate <= l_rate:
                return ret
            sql += f" (rate > {l_rate} and rate <= {c_rate})"
        if trade == 'buy':
            if c_rate >= l_rate:
                return ret
            sql += f" (rate >= {c_rate} and rate < {l_rate})"

        rs = self.cur.execute(sql).fetchone()
        #print(f"{rs}:{sql}")
        if rs != None:
            count = rs['count'] + 1
            seqnum = rs['seqnum']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"update trigger set count={count},updated_at='{timestamp}'"\
                + f" where seqnum={seqnum}"
            self.cur.execute(sql)
            self.conn.commit()
            ret = True
        return ret
#
#  method :: '(gx|dx)SIG(1.[0-9])
#
    def get_targetRate(self, trade, method, towsig, std):
        t_rate = towsig        # +2σ
        if len(method) > len('xxSIG') and is_float(method[5:]):
            sig = 2.0 - float(method[5:])
            #print(f">get_targetRate:sig={sig:5.3f}")
            if trade == 'sell':  
                t_rate = towsig - std*sig        # +1.[0-9]σ
            else:
                t_rate = towsig + std*sig        # +1.[0-9]σ
        #
        return t_rate
#
# 自動取引（売り）のトリガーチェック
#       c_rate: 現在のレート
#       l_rate: 前回のレート
#      
    def check_sell_tradeRate(self, symbol, c_rate, l_rate):
        #
        sql = "select * from trigger where "\
            + f"trade='sell' and symbol='{symbol}' and count <> 2"        
        rs = self.cur.execute(sql).fetchone()
        #
        rsAry = []
        while rs != None:
            if rs['exchange'] != '*' :
                rsAry.append( {'seqnum':rs['seqnum'],\
                               'exchange':rs['exchange'],\
                               'method':rs['method'].upper(),\
                               'exectype':rs['exectype'],\
                               'rate':rs['rate'],\
                               'amount': rs['amount'],\
                               'count':rs['count'],\
                               'histgram':rs['histgram'],\
                               'continuing':rs['continuing']} )
            #
            # read next record
            rs = self.cur.fetchone()
        #
        ret = None
        method = ''
        b_rate = 0.0
        count = countA = 0
        #
        for rs in rsAry:
            seqnum = rs['seqnum']
            b_rate = t_rate = rs['rate']            # 取引基準レート
            countA = count = rs['count']
            hist = rs['histgram']
            cont = rs['continuing']
            method = rs['method'].upper()           # 自動取引シナリオ
            #print(f"sell:{t_rate}:{method}:{l_rate} -> {c_rate}")
            exchange = rs['exchange']               # 取引所
            if b_rate <= 0.0:
                # 直近の買いレート
                max_rate = self.get_maxOrderBuyRate(exchange, symbol)
                #print(f"max_rate:{max_rate}")
            #
            if 'IM' in method:              # 指値
                if b_rate <= 0.0:
                    # 直近の買いレートの割り増し
                    if max_rate != None:
                        t_rate = max_rate*(1.0 + abs(b_rate))
                    else:
                        t_rate = 0.0
                else:
                    t_rate = b_rate
                #print(f"({method}):t_rate={t_rate}")
                if c_rate >= t_rate and t_rate > l_rate:
                    # 目標レートを超えた
                    countA = 2
                    ret = rs
                    #break
            elif 'DX' in method:            # MACD デッドクロス
                # 統計値の取得
                signe = self.get_macd_signe(symbol)
                #
                if 'SIG' in method:
                    if b_rate < 0.0:                     
                        # 直近の買いレートの割り増し
                        if max_rate != None:
                            b_rate = max_rate*(1.0 + abs(b_rate))
                        else:
                            b_rate = 0.0
                            countA = 0
                            #print(f"({method}):target rate not found.")
                    # 目標レートの設定
                    t_rate = self.get_targetRate('sell', method, signe['upper'], signe['std'])
                    if b_rate > t_rate:
                        t_rate = b_rate
                else:
                    if b_rate <= 0.0:                     
                        # 直近の買いレートの割り増し
                        if max_rate != None:
                            b_rate = max_rate*(1.0 + abs(b_rate))
                        else:
                            b_rate = 0.0
                            countA = 0
                            #print(f"({method}):target rate not found.")
                    t_rate = b_rate
                #print(f"({method}):t_rate={t_rate}")
                #
                if t_rate != 0.0 and (c_rate >= t_rate):
                    if count == 0  and t_rate > l_rate:
                        # 目標レートを超えた
                        if signe['histgram'] > 0:
                            self.print_signal(signe, hist)
                            #
                            countA = 1
                            hist = 0.0
                            cont = 0
                            #break
                    elif count == 1:
                        self.print_signal(signe, hist)
                        #
                        if abs(signe['histgram']) <= abs(hist):
                            # ヒストグラムの連続減少回数のカウントアップ
                            # ヒストグラム：MACDとシグナル線の乖離
                            cont += 1 
                        else:
                            cont = 0
                        hist = signe['histgram']
                        if ( hist <= 0 or (hist > 0 and cont >= hist_continuing)):
                            # デッドクロスを超えた、又は指定回数連続してヒストグラムの減少
                            countA = 2
                            ret = rs      # 「売り」の実行トリガー
                        #break
                else:
                    if t_rate != 0.0 and count == 1:
                        # 目標レートを下回った
                        countA = 0
                    #break
            #
            if countA != count or ( ('DX' in method) and count == 1 ):
                # update the control parmeter-count, histgram, continuing in trigger-table
                if countA != count or cont != 0:
                    self.print_state_change(ret, count, countA, cont, \
                                seqnum, symbol, 'Sell', method, b_rate, t_rate)
                #
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = f"update trigger set count={countA},"\
                    + f"histgram={hist},continuing={cont},updated_at='{timestamp}'"\
                    + f" where seqnum={seqnum}"
                self.cur.execute(sql)
                self.conn.commit()
            #
            if ret != None:
                # 実行条件に合致したトリガーがあった！！
                break
        return ret
#
# 自動取引（買い）のトリガーチェック
#         
    def check_buy_tradeRate(self, symbol, c_rate, l_rate):
        #
        sql = "select * from trigger where "\
            + f"trade='buy' and symbol='{symbol}' and count <> 2"        
        rs = self.cur.execute(sql).fetchone()
        #
        rsAry = []
        while rs != None:
            if rs['exchange'] != '*' :
                #
                rsAry.append( {'seqnum':rs['seqnum'],\
                               'exchange':rs['exchange'],\
                               'method':rs['method'].upper(),\
                               'exectype':rs['exectype'],\
                               'rate':rs['rate'],\
                               'amount': rs['amount'],\
                               'count':rs['count'],\
                               'histgram':rs['histgram'],\
                               'continuing':rs['continuing']} )
            # read next record
            rs = self.cur.fetchone()
        #print(len(rsAry))
        #
        ret = None
        count = countA = 0
        method = ''
        b_rate = 0.0
        #
        for rs in rsAry:
            seqnum = rs['seqnum']
            b_rate = t_rate = rs['rate']
            countA = count = rs['count']
            hist = rs['histgram']
            cont = rs['continuing']
            method = rs['method'].upper()
            #print(f"buy :{t_rate}:{method}:{l_rate} -> {c_rate}")
            exchange = rs['exchange']
            if b_rate <= 0.0:                     
                # 直近の売りレート
                min_rate = self.get_minOrderSellRate(exchange, symbol)
                #print(f"min_rate:{min_rate}")
            #
            if 'IM' in method:          # 指値
                if b_rate <= 0.0:                     
                    # 直近の売りレートから割引
                    if min_rate != None:
                        t_rate = min_rate*(1.0 - abs(b_rate))
                    else:
                        t_rate = 0.0
                else:
                    t_rate = b_rate
                #print(f"({method}):t_rate={t_rate}")
                if c_rate <= t_rate and t_rate < l_rate:
                    # 目標レートを下回った
                    countA = 2
                    ret = rs
                    #break
            elif 'GX' in method:        # MACD ゴールデンクロス
                # 統計値の取得
                signe = self.get_macd_signe(symbol)
                if 'SIG' in method:
                    if b_rate < 0.0:                     
                        # 直近の売りレートから割引
                        if min_rate != None:
                            b_rate = min_rate*(1.0 - abs(b_rate))
                        else:
                            b_rate = 0.0
                            countA = 0
                            #print(f"({method}):target rate not found.")
            # 目標レートの設定
                    t_rate = self.get_targetRate('buy', method, signe['lower'], signe['std'])
                    if (b_rate < t_rate) and b_rate != 0.0:
                        t_rate = b_rate
                else:
                    if b_rate <= 0.0:                     
                        # 直近の売りレートから割引
                        if min_rate != None:
                            b_rate = min_rate*(1.0 - abs(b_rate))
                        else:
                            b_rate = 0.0
                            countA = 0
                            #print(f"({method}):target rate not found.")
                    t_rate = b_rate
                #print(f"({method}):t_rate={t_rate}")
                #
                if c_rate <= t_rate:
                    if count == 0  and t_rate < l_rate:
                        # 目標レートを下回った
                        if signe['histgram'] < 0:
                            self.print_signal(signe, hist)
                            #
                            countA = 1
                            hist = 0.0
                            cont = 0
                            #break
                    elif count == 1:
                        self.print_signal(signe, hist)
                        #
                        if abs(signe['histgram']) <= abs(hist):
                            # ヒストグラムの連続減少回数のカウントアップ
                            # ヒストグラム：MACDとシグナル線の乖離
                            cont += 1 
                        else:
                            cont = 0
                        hist = signe['histgram']
                        if ( hist >= 0 or (hist < 0 and cont >= hist_continuing)):
                            # ゴールデンクロスを超えた、又は指定回数連続してヒストグラムの減少
                            countA = 2
                            ret = rs      # 「買い」の実行トリガー 
                        #break
                else:
                    if t_rate != 0.0 and count == 1:
                        # 目標レートを超えた
                        countA = 0
                    #break
            #
            if countA != count or ( ('GX' in method) and count == 1 ):
                # update the control parmeter-count 
                if countA != count or cont != 0:
                    self.print_state_change(ret, count, countA, cont, \
                                seqnum, symbol, 'Buy', method, b_rate, t_rate)
                #
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = f"update trigger set count={countA},"\
                    + f"histgram={hist},continuing={cont},updated_at='{timestamp}'"\
                    + f" where seqnum={seqnum}"
                self.cur.execute(sql)
                self.conn.commit()
            # 
            if ret != None:
                # 実行条件に合致したトリガーがあった！！
                break
        #
        return ret
#
#
#
    def pandas_read_ratelogs(self, params):
        if params['sym'] == '*':
            sql ="select * from ratelogs where length(symbol) < 6"
        else:
            sql ="select * from ratelogs where symbol = :sym"
        if params['limit'] > 0:
            sql += " LIMIT :limit"
        # return pandas.read_sql_query(sql, con=self.conn, params=params)
        return pandas.read_sql_query(sql, con=self.conn, index_col='inserted_at',\
                                     parse_dates=('inserted_at'), params=params)
#
# calculate MACD or other parameters.
#
    def get_macd_signe(self, symbol):
        # read rate-data from db to pandas
        params = {'sym':symbol, 'limit':0}
        df = self.pandas_read_ratelogs( params )
         # convert to OHLC
        mdf = df['rate'].resample('H').ohlc()
        mdf.columns = ['Open', 'High', 'Low', 'Close']
        # fill Non data with left col
        mdfil = mdf.fillna(method = 'ffill',inplace = False)
        # SMA
        mdfil["sma25"] = mdfil["Close"].rolling(window=25).mean()
        # STD
        mdfil["std"] = mdfil["Close"].rolling(window=25).std(ddof=1)
        # EMA
        mdfil["ema12"] = mdfil["Close"].ewm(span=12,adjust=False).mean()
        mdfil["ema26"] = mdfil["Close"].ewm(span=26,adjust=False).mean()
        # MACD,SIGNAL
        mdfil["macd"] = mdfil["ema12"] - mdfil["ema26"]
        mdfil["signal"] = mdfil["macd"].ewm(span=9,adjust=False).mean()

        # get Series from DataFrame and latest datas.
        macdSer = mdfil["macd"]
        signalSer = mdfil["signal"]
        histgram = macdSer[-1] - signalSer[-1] 
        #
        samSer = mdfil["sma25"]
        stdSer = mdfil["std"]
        upper = samSer[-1] + stdSer[-1] * 2 
        lower = samSer[-1] - stdSer[-1] * 2 
        #
        return { 'histgram': histgram, 'upper':upper, 'lower':lower, 'std':stdSer[-1]}
#
# delete the rate-logs before the specified datetime.
#
    def delete_ratelogs(self, last_datetime):
        #print(last_datetime)
        last_time_epoch = int(time.mktime(last_datetime.timetuple()))
        sql = "delete from ratelogs where "\
            + f"time_epoch < {last_time_epoch}"
        print(sql)
        self.cur.execute(sql)
        self.conn.commit()
        return

#
# print out signal-data.
#
    def print_signal(self, signe, hist):
        if ( abs(signe['histgram'])) < abs(hist):
            print_text = colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"   >hist={signe['histgram']:12.3f},")
            print_text += colored_reset()
        elif signe['histgram'] < 0.0:
            print_text = colored_16(STYLE_NON,FG_RED,BG_BLACK,f"   >hist={signe['histgram']:12.3f},")
            print_text += colored_reset()
        else:
            print_text = f"   >hist={signe['histgram']:12.3f},"

        print_text += f" std={signe['std']:12.3f}, "\
                   + f"upper={signe['upper']:12.3f}, lower={signe['lower']:12.3f}"
        print(print_text)
        return

#
# edit print-out text for continuing-data.
#
    def edit_cont_text(self, cont):
        if cont == 0:
            cont_text = f"  cont={cont}"
        elif cont == 5:
            cont_text = colored_16(STYLE_NON,FG_RED,BG_BLACK,f"  cont={cont}")
        elif cont == 4:
            cont_text = colored_16(STYLE_BLINK,FG_RED,BG_BLACK,f"  cont={cont}")
        elif cont == 1:
            cont_text = colored_16(STYLE_NON,FG_YELLOW,BG_BLACK,f"  cont={cont}")
        else:
            cont_text = colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"  cont={cont}")
        return cont_text
    #
#
# print the state(count)-change of trade trigger.
#
    def print_state_change(self, rslt, b_count, a_count, cont, seq, sym, trade, method, b_rate, t_rate):
        print_text =''
        if rslt == None:
            rslt = False
        else:
            rslt = True
        #
        if a_count == 1:
            print_text = colored_16(STYLE_NON,FG_YELLOW,BG_BLACK,f"")
        elif a_count == 2:
            print_text = colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"")
        elif a_count == 0 and b_count == 1:
            print_text = colored_16(STYLE_NON,FG_BLUE,BG_BLACK,f"")
        #
        print_text += f"   >{trade}({sym}):{rslt}:{b_count}->{a_count}:"\
                    + f"seq={seq}:{method}({b_rate:,.3f}):t_rate={t_rate:13,.3f}:"
        print(print_text + self.edit_cont_text(cont) + colored_reset())
        return

#eof
