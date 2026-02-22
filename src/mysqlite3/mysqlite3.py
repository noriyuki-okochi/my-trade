#
#
# Class for sqlite3
#     
import sqlite3
import pandas
import time
import myApi as my
from env import *
from datetime import datetime
#
# Private API Class for sqlite3from env import *
#
class MyDb:
    def __init__(self, dbpath='../Auto-trade.db', logwrite = False):
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.logfile = None
        if logwrite:
            timestamp = datetime.now().strftime('%Y%m%d')
            self.logfile = open(dbpath[:dbpath.rfind('/')+1] + f"log{timestamp}.txt", 'a')
            #self.logfile.write(f"DB opened: {dbpath}\n")
            #self.logfile.flush()

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
        symbol = symbol.lower()
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
        symbol = symbol.lower()
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"

        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            amount = rs['amount']

        print(f">get_balanceAmount=>amount={amount}:sql={sql}")
        return amount
#
# select amount from orders-table
#
    def get_targetAmount(self, exchange, symbol, target):
        symbol = symbol.upper()
        # get id of latest sell-order
        sql = "select id from orders where order_side='SELL' "\
            + f"and exchange='{exchange}' and pair='{symbol}' order by id desc limit 1"
        rs = self.cur.execute(sql).fetchone()
        #
        amount = None
        sql = "select sum(amount) as sell_amount from orders where order_side='BUY' "\
            + f"and rate<={target} and exchange='{exchange}' and pair='{symbol}'"
        if rs != None:
            sql += f" and id >{rs['id']}"
        sql += " order by id desc"
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            amount = rs['sell_amount']
        print(f">get_targetAmount=>amount={amount}:sql={sql}")
        return amount
#
# adjust amount 
#  
    def adjust_balance(self, exchange, symbol, trade, amount):
        symbol = symbol.lower()        
        c_amount = self.get_balanceAmount(exchange, symbol)
        if c_amount != None:
            if trade == 'SELL':
                c_amount -= amount
            else:     # 'BUY'
                c_amount += amount
            sql = f"update balance set amount = {c_amount} where "\
                + f"exchange='{exchange}' and symbol='{symbol}'"

            print(f">adjust_balance:sql={sql}")
            self.cur.execute(sql)
            self.conn.commit()            
        return c_amount
#
# insert samplling rates logs.
#
    def insert_ratelogs(self, exchange, symbol, rate, id=0, timestamp=None):
        if timestamp == None:
            d = datetime.now()
            timestamp = d.strftime('%Y-%m-%d %H:%M:%S')
        else:
            d = datetime.strptime(timestamp,'%Y-%m-%d %H:%M:%S')
        time_epoc = int(time.mktime(d.timetuple()))
        sql = "insert into ratelogs"\
            + "(exchange,symbol,rate,id,inserted_at,time_epoch) values("\
            + f"'{exchange}',"\
            + f"'{symbol}',"\
            + f"{rate},"\
            + f"{id},"\
            + f"'{timestamp}',"\
            + f"{time_epoc})"
        self.cur.execute(sql)
        self.conn.commit()
#
# insert auto-orders log
#
    def insert_orders(self, id, exchange, pair, trade, extype, rate, amount):
        # insert new datas
        sql = "insert into orders(id, exchange, pair, order_side, order_type, rate, amount)"
        sql += f" values({id},'{exchange}','{pair}','{trade}','{extype}',{rate},{amount})"
        #print(sql)
        self.cur.execute(sql)
        #
        self.conn.commit()
#
# modify the rate of ratelogs by one of orders.
#
    def modify_rateLogsByOrders(self, exchange, sym, timestamp):
        # create coursor to update
        cur1 = self.conn.cursor()
        count = 0
        sql = "select rate, id from orders where "\
            + f"exchange='{exchange}' and created_at >='{timestamp}'"
        if sym != None:
            sql += f" and pair='{sym.upper()}'"
        #print(sql)
        rs = self.cur.execute(sql).fetchone()
        while rs != None:
            sql = f"update ratelogs set rate={rs['rate']} where id={rs['id']}"
            print(f">{sql}")
            cur1.execute(sql)
            self.conn.commit()
            count += 1
            #
            # read next record
            rs = self.cur.fetchone()
        cur1.close()
        self.cur.close()
        #
        return count       
#
# select the max rate from recent buy-orders-log
#
    def get_maxOrderBuyRate(self, exchange, pair):
        result = None
        # select last sell-record
        sql = "select id,rate from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'SELL' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            id = rs['id']
            rate = rs['rate']
            sql = "select max(rate) as max_rate from orders where "
            sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'BUY' "
            sql += f" and id > {id}"
            #print(sql)
            self.cur.execute(sql)
            rs = self.cur.execute(sql).fetchone()
            if rs != None:
                result = rs['max_rate']
            else:
                result = rate
            #print(f"get_maxOrderBuyRate:{result}")
        return result
#
# select the last rate from recent buy-orders-log
#
    def get_lastOrderBuyRate(self, exchange, pair):
        result = None
        # select last sell-record
        sql = "select * from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'BUY' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            result = rs['rate']
        return result
#
#
# select the min rate from recent sell-orders-log
#
    def get_minOrderSellRate(self, exchange, pair):
        result = None
        # select last buy-record
        sql = "select id,rate from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'BUY' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            id = rs['id']
            rate = rs['rate']
            sql = "select min(rate) as min_rate from orders where "
            sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'SELL' "
            sql += f" and id > {id}"
            #print(sql)
            self.cur.execute(sql)
            rs = self.cur.execute(sql).fetchone()
            if rs != None:
                result = rs['min_rate']
            else:
                result = rate
            #print(f"get_minOrderSellRate:{result}")
        return result
#
# select the last rate from recent sell-orders-log
#
    def get_lastOrderSellRate(self, exchange, pair):
        result = None
        # select last buy-record
        sql = "select * from orders where "
        sql += f" exchange = '{exchange}' and pair = '{pair.upper()}' and order_side = 'SELL' "
        sql += f" order by id desc  limit 1"
        #print(sql)
        self.cur.execute(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            result = rs['rate']
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
    def get_benefit(self, exchange, pair, fdate, tdate, crate):
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
            amtb = rs['AMT']
            rate = benefit/amtb
            count = rs['CNT']
            print(f">Buy ={benefit:,}({amtb:.4f} x {rate:.3f}) <{count}>")
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
                amts = rs['AMT']
                rate = jpy/amts
                count = rs['CNT']
                print(f">SELL={jpy:,}({amts:.4f} x {rate:.3f}) <{count}>")
                #
                print(f">BeneFit={(jpy - benefit):,}({((jpy - benefit)*100/benefit):.2f}%)")
                if amtb > amts:
                    amt = amtb - amts
                    print(f">{pair}_jpy:{int(amt*crate):,}({amt:.4f})")                
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
# delete the record with id in orders-log and ratelogs
#
    def delete_order(self, exchange, order_id):
        sql = f"delete from orders where exchange='{exchange}' and id={order_id}"
        print(sql)
        self.cur.execute(sql)
        sql = f"delete from ratelogs where exchange='{exchange}' and id={order_id}"
        print(sql)
        self.cur.execute(sql)
        self.conn.commit()
#
# update the trigger/orders-table
#
    def update_any(self, table, keyVal, item, value):
        #
        if table == 'trigger':
            prmKey = 'seqnum'
        elif table == 'orders':       # 'orders'
            prmKey = 'id'
        else:       # 'ratelogs'
            prmKey = 'seqnum'
        #
        if item in ['method', 'exectype']:
            sql = f"update {table} set {item}='{value}' where {prmKey}={keyVal}"
        elif item == 'at':      # inserted_at
            sql = f"update {table} set inserted_at='{value}' where {prmKey}={keyVal}"
        else:
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
    def insert_trigger(self, symbol, trade, ratelist, update):
        if update != 7:
            # delete old datas
            sql = "delete from trigger where "\
                + f"symbol='{symbol}' and trade='{trade}'"
            self.cur.execute(sql)
        # insert new datas
        for rate in ratelist:
            if update == 7:     # 先頭'!'を追加する
                if rate[0] != '!':
                    continue
                else:
                    rate = rate[1:]
            #print(f"insert_trigger:{rate}")
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
                if symbol.upper() == 'IOST':
                    exectype = 'LIMIT'
                else:
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
# get trigger info. for auto-trade
#   trigger :: '<target-rate>!<scenario>:<exchange-office>:<amount>'
#  
    def get_trigger(self, trigger):
        sql = f"select * from trigger where seqnum={trigger}"
        rs = self.cur.execute(sql).fetchone()
        #
        # store selected records to temporary array.
        #  
        info = None
        if rs != None:
            info = {'symbol':rs['symbol'],\
                     'exchange':rs['exchange'],\
                     'side':rs['trade'],\
                     'exectype':rs['exectype'],\
                     'rate':rs['rate'],\
                     'amount':rs['amount']}
        return info
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
#  トリガー指定のレートを超えているか判定して、countの初期設定を行う
#      
    def init_triggerCount(self, trade, symbol, c_rate, std_rate):
        print(f"init_triggerCount( {trade.upper()}, {symbol.upper()}, {c_rate:13.3f} ,{std_rate})")
        ret = False
        sql = "select * from trigger where "\
            + f"trade='{trade}' and symbol='{symbol}' and "\
            + f"count=0"
        rs = self.cur.execute(sql).fetchone()
        #
        # store selected records to temporary array.
        #  
        rsAry = []
        while rs != None:
            rsAry.append( {'seqnum':rs['seqnum'],\
                           'exchange':rs['exchange'],\
                           'method':rs['method'],\
                           'rate':rs['rate'] } )
            # read next record
            rs = self.cur.fetchone()

        # 統計値の取得
        sign = self.get_macd_sign(symbol)

        for rs in rsAry:
            exchange = rs['exchange']
            method = rs['method'].upper()
            b_rate = rs['rate']
            m_rate = None
            if b_rate < 0.0:
                if trade == 'sell':
                    if std_rate != None:
                        max_rate = float(std_rate)
                    else:
                        # 直近の買いレート
                        m_rate = self.get_maxOrderBuyRate(exchange, symbol)
                    if m_rate == None:
                        b_rate = 0
                    else:
                        b_rate = m_rate*(1.0 + abs(b_rate))
                else:
                    if std_rate != None:
                        max_rate = float(std_rate)
                    else:
                        # 直近の売りレート
                        m_rate = self.get_minOrderSellRate(exchange, symbol)
                    if m_rate == None:
                        b_rate = 0
                    else:
                        b_rate = m_rate*(1.0 - abs(b_rate))
            #
            update_flg = False
            if method == 'IM':
                t_rate = b_rate
                if trade == 'sell' and t_rate > 0.0 and c_rate >= t_rate:
                    update_flg = True
                if trade == 'buy' and t_rate > 0.0 and c_rate <= t_rate:
                    update_flg = True
            elif 'SIG' in method:
                # 目標レートの設定
                if trade == 'sell':
                    t_rate = self.get_targetRate('sell', method, sign['upper'], sign['std'])
                    if b_rate != 0 and b_rate > t_rate:
                        t_rate = b_rate
                    if t_rate > 0.0 and c_rate >= t_rate:
                        update_flg = True
                else:
                    t_rate = self.get_targetRate('buy', method, sign['lower'], sign['std'])
                    if b_rate != 0 and b_rate < t_rate:
                        t_rate = b_rate
                    if t_rate > 0.0 and c_rate <= t_rate:
                        update_flg = True
            #
            seqnum = rs['seqnum']
            print(f"({seqnum}){method:10}:{update_flg}:rate={rs['rate']},"\
                  +  f"b_rate={b_rate:13.3f}, t_rate={t_rate:13.3f}, m_rate={m_rate}")
            if update_flg == True:
                # update count 
                count = 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = f"update trigger set count={count},updated_at='{timestamp}'"\
                    + f" where seqnum={seqnum}"
                self.cur.execute(sql)
                print(f"Trigger({seqnum}) count initialized to 1.")
                ret = True
        #
        if ret == True:
            self.conn.commit()
            #print(f"Trinit_triggerCount:committed.")
        return ret
#
#  登録済トリガーの表示
#      
    def print_trigger(self, trade, symbol):
        #print(f"print_trigger( {trade.upper()}, {symbol.upper()})")
        header = True
        sql = "select * from trigger where "\
            + f"trade='{trade.lower()}' and symbol='{symbol.lower()}'"
        rs = self.cur.execute(sql).fetchone()
        while rs != None:
            if header == True:
                print(f"--{symbol.upper()}({trade.upper()})--")
                header = False
            exchange = rs['exchange']
            method = rs['method'].upper()
            b_rate = rs['rate']
            amount = rs['amount']
            count = rs['count']
            cont = rs['continuing']
            print(f"  {rs['seqnum']} {exchange:<9}:{method:<10}:{b_rate} ,{amount} ({count}:{cont})")
            # read next record
            rs = self.cur.fetchone()
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
        if len(method) > len('xxSIG') and my.is_float(method[5:]):
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
    def check_sell_tradeRate(self, symbol, c_rate, l_rate, std_rate):
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
                               'continuing':rs['continuing'],\
                               'target':None} )
            #
            # read next record
            rs = self.cur.fetchone()
        #
        ret = None
        method = ''
        b_rate = 0.0
        count = countA = 0
        hist_cont_m = int(hist_cont_l_s[auto_coin_symbols.index(symbol)])
        pct_volat_m = float(pct_volat[auto_coin_symbols.index(symbol)])
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
            if b_rate < 0.0:
                if std_rate != None:
                    max_rate = float(std_rate)
                else:
                    # 直近の買いレート
                    max_rate = self.get_maxOrderBuyRate(exchange, symbol)
            #
            if 'IM' in method:              # 指値
                if b_rate < 0.0:
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
                sign = self.get_macd_sign(symbol)
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
                    t_rate = self.get_targetRate('sell', method, sign['upper'], sign['std'])
                    if b_rate > t_rate:
                        t_rate = b_rate
                else:
                    if b_rate < 0.0:                     
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
                        if sign['histgram'] > 0:
                            self.print_signal(sign, hist)
                            #
                            countA = 1
                            hist = 0.0
                            cont = 0
                            #break
                    elif count == 1:
                        self.print_signal(sign, hist)
                        #
                        if abs(sign['histgram']) <= abs(hist):
                            # ヒストグラムの連続減少回数のカウントアップ
                            # ヒストグラム：MACDとシグナル線の乖離
                            cont += 1 
                        else:
                            cont = 0
                        hist = sign['histgram']
                        volat = sign['volat']
                        if ( hist <= 0 or (hist > 0 and cont >= hist_cont_m) and \
                             not (b_rate == 0.0 and volat < pct_volat_m) ):
                            # デッドクロスを超えた、又は指定回数連続してヒストグラムの減少
                            countA = 2
                            rs['target'] = t_rate
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
                    self.print_state_change(ret, count, countA, cont, hist_cont_m, \
                                seqnum, symbol, 'Sell', method, b_rate, t_rate, exchange)
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
    def check_buy_tradeRate(self, symbol, c_rate, l_rate, std_rate):
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
                               'continuing':rs['continuing'],\
                               'target':None} )
            # read next record
            rs = self.cur.fetchone()
        #print(len(rsAry))
        #
        ret = None
        count = countA = 0
        method = ''
        b_rate = 0.0
        hist_cont_m = int(hist_cont_l_b[auto_coin_symbols.index(symbol)])
        pct_volat_m = float(pct_volat[auto_coin_symbols.index(symbol)])
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
            if b_rate < 0.0:                     
                if std_rate != None:
                    min_rate = float(std_rate)
                else:
                    # 直近の売りレート
                    min_rate = self.get_minOrderSellRate(exchange, symbol)
            #
            if 'IM' in method:          # 指値
                if b_rate < 0.0:                     
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
                sign = self.get_macd_sign(symbol)
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
                    t_rate = self.get_targetRate('buy', method, sign['lower'], sign['std'])
                    if (b_rate < t_rate) and b_rate != 0.0:
                        t_rate = b_rate
                else:
                    if b_rate < 0.0:                     
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
                        if sign['histgram'] < 0:
                            self.print_signal(sign, hist)
                            #
                            countA = 1
                            hist = 0.0
                            cont = 0
                            #break
                    elif count == 1:
                        self.print_signal(sign, hist)
                        #
                        if abs(sign['histgram']) <= abs(hist):
                            # ヒストグラムの連続減少回数のカウントアップ
                            # ヒストグラム：MACDとシグナル線の乖離
                            cont += 1 
                        else:
                            cont = 0
                        hist = sign['histgram']
                        volat = sign['volat']
                       #pct = sign['pct']
                        #if ( hist >= 0 or (hist < 0 and cont >= hist_cont_m and pct >= 0.0)):
                        if ( hist >= 0 or (hist < 0 and cont >= hist_cont_m) and \
                            not (b_rate == 0.0 and volat < pct_volat_m) ):
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
                    self.print_state_change(ret, count, countA, cont, hist_cont_m, \
                                seqnum, symbol, 'Buy', method, b_rate, t_rate, exchange)
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
        #print(f"pandas_read_ratelogs:{params}:{sql}")
        return pandas.read_sql_query(sql, con=self.conn, index_col='inserted_at',\
                                     parse_dates=('inserted_at'), params=params)
#
# calculate MACD or other parameters.
#
    def get_macd_sign(self, symbol):
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
        # 
        # Volatility
        mdfil["volat"] = mdfil["High"] - mdfil["Low"]
        mdfil["volat"] = mdfil["volat"] / mdfil["Open"]
        mdfil["vsma"] = mdfil["volat"].rolling(window=prd_volat).mean()

        '''
        for col_name, itemSer in mdfil.items():
            if col_name == idx_change:
                mdfil["pct"] = itemSer
                # 変化率の計算
                mdfil["pct"] = mdfil["pct"].pct_change(prd_change).fillna(method = 'bfill')

        '''        
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
        volatSer = mdfil["vsma"]
        '''
        if 'pct' in mdfil.columns:
            pctSer = mdfil["pct"]
        else:
            pctSer = None
            print(f"{idx_change} is not found in columns")
        '''
        #
        return { 'histgram': histgram, 'upper':upper, 'lower':lower, 'std':stdSer[-1], 'volat':volatSer[-1] }
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
    def print_signal(self, sign, hist):
        if ( abs(sign['histgram'])) < abs(hist):
            print_text = my.colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"   >hist={sign['histgram']:12.3f},")
            print_text += my.colored_reset()
        elif sign['histgram'] < 0.0:
            print_text = my.colored_16(STYLE_NON,FG_RED,BG_BLACK,f"   >hist={sign['histgram']:12.3f},")
            print_text += my.colored_reset()
        else:
            print_text = f"   >hist={sign['histgram']:12.3f},"

        print_text += f" std={sign['std']:12.3f}, "\
                   + f"upper={sign['upper']:12.3f}, lower={sign['lower']:12.3f}, volat={sign['volat']:.4f}"
        print(print_text)
        #
        # logwrite
        # 
        print_text = f" >hist={sign['histgram']:12.3f}, volat={sign['volat']:.4f}"
        self.logwrite(print_text)   
        return

#
# edit print-out text for continuing-data.
#
    def edit_cont_text(self, cont, cont_m):
        if cont == 0:
            cont_text = f"  cont={cont}/{cont_m}"
        elif cont == cont_m:
            cont_text = my.colored_16(STYLE_NON,FG_RED,BG_BLACK,f"  cont={cont}/{cont_m}")
        elif cont == (cont_m - 1):
            cont_text = my.colored_16(STYLE_BLINK,FG_RED,BG_BLACK,f"  cont={cont}/{cont_m}")
        elif cont == 1:
            cont_text = my.colored_16(STYLE_NON,FG_YELLOW,BG_BLACK,f"  cont={cont}/{cont_m}")
        else:
            cont_text = my.colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"  cont={cont}/{cont_m}")
        return cont_text
    #
#
# print the state(count)-change of trade trigger.
#
    def print_state_change(self, rslt, b_count, a_count, cont, cont_m, seq, sym, trade, method, b_rate, t_rate, exchange):
        print_text =''
        if rslt == None:
            rslt = False
        else:
            rslt = True
        #
        trade = trade.upper()
        msg = f"{trade}({sym}):{rslt}:{b_count}->{a_count}:"\
            + f"seq={seq}:{method:<10}({b_rate:,.3f}):t_rate={t_rate:13,.3f}:"\
            + f" {exchange}"
        #
        # display msg
        #
        if a_count == 1:
            print_text = my.colored_16(STYLE_NON,FG_YELLOW,BG_BLACK,f"")
        elif a_count == 2:
            print_text = my.colored_16(STYLE_NON,FG_GREEN,BG_BLACK,f"")
        elif a_count == 0 and b_count == 1:
            print_text = my.colored_16(STYLE_NON,FG_BLUE,BG_BLACK,f"")
        #
        print_text += f"   >{msg}"
        print(print_text + self.edit_cont_text(cont, cont_m) + my.colored_reset())
        #
        # logwrite msg
        #
        self.logwrite(f" :{msg} cont={cont}/{cont_m}")   
        return
#
# logout
#
    def logwrite(self, msg):
        if self.logfile is not None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.logfile.write(f"{timestamp}{msg}\n")
            self.logfile.flush()

###############################################################################################################
# delete the trade_history.
#
    def delete_trade_history(self, exchange: str):
        if exchange == 'coincheck':
            table_name = 'coincheck_trade_history'
        elif exchange == 'gmocoin':
            table_name = 'gmocoin_trade_history'
        else:
            print(f"[delete_trade_history]error: exchange '{exchange}' not supported.")
            return False
        
        sql = f"delete from {table_name}"
        print(sql)
        self.cur.execute(sql)
        self.conn.commit()
        return True
#
# agregate the sales_history.
#
    def agregate_trade_sales(self, exchange: str):
        cond_str = None
        if exchange == 'coincheck':
            table_name = 'coincheck_trade_history'
            sel_items = "通貨ペア as symbol,取引種別 as side,SUM(増加数量) as in_amount,SUM(減少数量) as out_amount,SUM(手数料数量) as fee"
            grp_items = "通貨ペア,取引種別"
            cond_str = "取引種別 in ('購入','売却')"
        elif exchange == 'gmocoin':
            table_name = 'gmocoin_trade_history'
            sel_items = "銘柄名 as symbol,売買区分 as side,SUM(約定数量) as amount,SUM(約定金額) as jpy,SUM(注文手数料) as fee"
            grp_items = "銘柄名,売買区分"
            cond_str = "売買区分 is not null"
        else:
            print(f"[agregate_trade_history]error: exchange '{exchange}' not supported.")
            return False
        #
        sql = f"SELECT {sel_items} FROM {table_name} WHERE {cond_str} GROUP BY {grp_items}"
        #print(sql)
        return pandas.read_sql_query(sql, con=self.conn)

#
# agregate the otheres_history.
#
    def agregate_trade_otheres(self, exchange: str):
        cond_str = None
        if exchange == 'coincheck':
            table_name = 'coincheck_trade_history'
            sel_items = "増加通貨名 as symbol,取引種別 as side,SUM(増加数量) as in_amount"
            grp_items = "増加通貨名,取引種別"
            cond_str = "取引種別 in ('受取')"
        elif exchange == 'gmocoin':
            table_name = 'gmocoin_trade_history'
            sel_items = "銘柄名 as symbol,授受区分 as side,SUM(数量) as amount"
            grp_items = "銘柄名,授受区分"
            cond_str = "精算区分 in ('暗号資産預入・送付')"
        else:
            print(f"[agregate_trade_history]error: exchange '{exchange}' not supported.")
            return False
        #
        sql = f"SELECT {sel_items} FROM {table_name} WHERE {cond_str} GROUP BY {grp_items}"
        #print(sql)
        return pandas.read_sql_query(sql, con=self.conn)
#
# gmo_return_fee.
#
    def gmo_return_fee(self):
        cond_str = None
        table_name = 'gmocoin_trade_history'
        sel_items = "銘柄名 as symbol,精算区分,SUM(日本円受渡金額) as jpy"
        grp_items = "銘柄名,精算区分"
        cond_str = "精算区分 in ('取引所現物 取引手数料返金')"
        #
        sql = f"SELECT {sel_items} FROM {table_name} WHERE {cond_str} GROUP BY {grp_items}"
        #print(sql)
        return pandas.read_sql_query(sql, con=self.conn)
#
# read account_statement.
#    
    def pandas_read_account(self, key_t: tuple):
        exchange, symbol, year = key_t
        sql =f"select * from account_statement where account_year={year} and symbol='{symbol}' and exchange='{exchange}'"
        print(sql)
        return pandas.read_sql_query(sql, con=self.conn)

#
# update account_statement.
#    
    def update_account_statement(self, key_t: tuple, data_d):
        ex, sym, year = key_t
        table_name = 'account_statement'
        sql = f"update {table_name} set "\
              f" buy_amount = {data_d['buy_amount']},"\
              f" buy_jpy = {data_d['buy_jpy']},"\
              f" sell_amount = {data_d['sell_amount']},"\
              f" sell_jpy = {data_d['sell_jpy']},"\
              f" receipt_amount = {data_d['receipt_amount']},"\
              f" receipt_jpy = {data_d['receipt_jpy']},"\
              f" send_amount = {data_d['send_amount']},"\
              f" send_jpy = {data_d['send_jpy']},"\
              f" f_carry_amount = {data_d['f_carry_amount']},"\
              f" f_carry_jpy = {data_d['f_carry_jpy']},"\
              f" e_carry_amount = {data_d['e_carry_amount']},"\
              f" e_carry_jpy = {data_d['e_carry_jpy']},"\
              f" average_unit = {data_d['average_unit']},"\
              f" sale_proceeds = {data_d['sale_proceeds']},"\
              f" sale_costs = {data_d['sale_costs']},"\
              f" fee = {data_d['fee']},"\
              f" income = {data_d['income']},"\
              f" note = '{data_d['note']}'"
        sql += f" where account_year = {year} and symbol = '{sym}' and exchange = '{ex}'"              
        print(sql)
        self.cur.execute(sql)
        self.conn.commit()
        return 
#    
# insert daily candlelogs.
# 
    def insert_candlelogs(self, symbol: str, last_date = None):
        params = {"sym": symbol.lower(), "limit": 0}
        #
        df = self.pandas_read_ratelogs(params)
        # convert to OHLC
        mdf = df['rate'].resample('D').ohlc()
        mdf.columns = ['open_rate', 'high_rate', 'low_rate', 'close_rate']
        mdfil = mdf.fillna(method = 'ffill',inplace = False)
        mdfil['symbol'] = symbol.upper()
        mdfil = mdfil.sort_index(ascending=True)
        if last_date is not None:
            # 指定日付以前（削除対象）のデータを追加対象とする
            mdfil = mdfil[mdfil.index < last_date]
        if mdfil.shape[0] == 0:
            print(f"insert_candlelogs:No new data to insert for {symbol}.")
        else:
            # 追加データの最古日付のレコードが既に登録されていれば、同日付のレコードを削除する。
            fdate = mdfil.index[0]
            delete_sql = f"delete from candlelogs where symbol='{symbol}' and date(inserted_at) = date('{fdate}')"
            print(delete_sql)
            self.cur.execute(delete_sql)
            self.conn.commit()
            # 日ローソク足データの追加
            mdfil.to_sql('candlelogs', self.conn, if_exists='append', index='inserted_at', method='multi', chunksize=1024)
            print(f"insert_candlelogs: {mdfil.shape[0]} new data to insert for {symbol}.")
        return mdfil.shape[0]
#
# calcurate jpy of otheres
#
    def calc_otheres_jpy(self, exchange: str, symbol: str, side: str):
        jpy = 0
        table2 = "candlelogs as t2"
        if exchange == 'coincheck':
            sel_item = "SUM(増加数量*close_rate) as jpy, SUM(増加数量) as amt"
            table1 = 'coincheck_trade_history as t1'
            on_str = "t1.増加通貨名 = t2.symbol AND DATE(t1.取引日時) = DATE(t2.inserted_at)"
            cond_str = f"t1.取引種別 in ('{side}') and t1.増加通貨名='{symbol}' GROUP BY t1.増加通貨名"
        elif exchange == 'gmocoin':
            sel_item = "SUM(数量*close_rate) as jpy, SUM(数量) as amt"
            table1 = "gmocoin_trade_history as t1"
            on_str = "t1.銘柄名 = t2.symbol AND DATE(t1.日時) = DATE(t2.inserted_at)"
            cond_str = f"t1.授受区分 in ('{side}') and t1.銘柄名='{symbol}' GROUP BY t1.銘柄名"
    #
        sql = f"SELECT {sel_item} FROM {table1} LEFT JOIN {table2} ON {on_str} WHERE {cond_str}"
        #print(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            jpy = rs['jpy']
            amt = rs['amt']
            print(f"calc_otheres_jpy:{exchange}:{symbol}:{side}:jpy={jpy}(amt={amt}, rate={jpy/amt if amt != 0 else 0:,.3f})")
        return jpy
#
# delete table-records
#
    def delete_trade_accounts_records(self, table, key_t):
        year, ex, sym = key_t
        cond_str = ''
        if ex != '*':
            cond_str = f"exchange='{ex}'"
        if sym != '*':
            if cond_str != '': cond_str += ' and '
            cond_str += f"symbol='{sym}'" 
        if year != '*':
            if cond_str != '': cond_str += ' and '
            if table ==  'account_statement':
                cond_str += f"account_year={year}"
            elif table ==  'candlelogs':
                cond_str += f"strftime('%Y',inserted_at)='{year}'"
            elif table == 'coincheck_trade_history':
                cond_str += f"strftime('%Y',取引日時)='{year}'"
            elif table == 'gmocoin_trade_history':
                cond_str += f"strftime('%Y',日時)='{year}'"
                
        if len(cond_str) > 0:
            cond_str = f" where {cond_str}"
        #
        sql = f"delete from {table} {cond_str}"
        print(sql)
        print(f"Are you sure?[y/n].")
        ans = input('>')
        if ans == 'y':
            self.cur.execute(sql)
            self.conn.commit()
        return
#eof
# 
