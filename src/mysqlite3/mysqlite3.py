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
        self.to_exchange = None
        self.exec_type = None
        self.exec_amount = None
        #self.l_histogram = None

    def rollback(self):
        self.conn.rollback()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def execute(self, sql):
        return self.cur.execute(sql)

    def toExchange(self):
        return self.to_exchange

    def execType(self):
        return self.exec_type

    def execAmount(self):
        return self.exec_amount

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
# update the order-rate of orders-log
#
    def update_orderRate(self, order_id,  rate):
        #print(f"update_orderRate:{order_id}({rate:9,.3f})")
        sql = f"update orders set rate={rate} where id={order_id}"
        self.cur.execute(sql)
        self.conn.commit()
#
# insert trigger info. for auto-trade
#  
    def insert_trigger(self, symbol, trade, ratelist):
        # delete old datas
        sql = "delete from trigger where "\
            + f"symbol='{symbol}' and trade='{trade}'"
        self.cur.execute(sql)
        # insert new datas
        for rate in ratelist:
            if rate[:1].isdigit() == True:
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
                if rate[0] == '-':
                    exectype = 'STOP'
                    rate = rate[1:]
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
    def check_tradeRate(self, trade, symbol, c_rate, l_rate):
        ret = False
        self.to_exchange = None
        self.exec_amount = None
        sql = "select * from trigger where "\
            + f"trade='{trade}' and symbol='{symbol}' and "\
            + f"count=0 and method='IM' and "
        if trade == 'sell':
            if c_rate <= l_rate:
                return ret
            sql += f" (rate > {l_rate} and rate <= {c_rate})"
        if trade == 'buy':
            if c_rate >= l_rate:
                return ret
            sql += f" (rate >= {c_rate} and rate < {l_rate})"

        #print(sql)
        rs = self.cur.execute(sql).fetchone()
        if rs != None:
            self.to_exchange = rs['exchange']
            self.exec_amount = rs['amount']
            self.exec_type = rs['exectype']
            count = rs['count']
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
    def check_sell_tradeRate(self, symbol, c_rate, l_rate):
        self.to_exchange = None
        self.exec_amount = None
        self.exec_type = None

        sql = "select * from trigger where "\
            + f"trade='sell' and symbol='{symbol}' and count <> 2"        
        rs = self.cur.execute(sql).fetchone()
        #
        ret = False
        method = ''
        b_rate = 0.0
        count = countA = 0
        #
        while rs != None:
            if rs['exchange'] != '*' :
                seqnum = rs['seqnum']
                b_rate = t_rate = rs['rate']
                countA = count = rs['count']
                hist = rs['histgram']
                cont = rs['continuing']
                method = rs['method'].upper()
                #print(f"sell:{t_rate}:{method}:{l_rate} -> {c_rate}")

                self.to_exchange = rs['exchange']
                self.exec_amount = rs['amount']
                self.exec_type = rs['exectype']
                #
                if 'IM' in method:
                    if c_rate >= t_rate and t_rate > l_rate:
                        # 目標レートを超えた
                        countA = 2
                        ret = True
                        break
                elif 'DX' in method:
                    # 統計値の取得
                    signe = self.get_macd_signe(symbol)
                    if 'SIG' in method:
                        # 目標レートの設定
                        t_rate = self.get_targetRate('sell', method, signe['upper'], signe['std'])
                        if b_rate != 0.0 and b_rate > t_rate:
                            t_rate = b_rate
                    elif b_rate == 0.0:                     
                        order = self.get_lastOrder(self.to_exchange, symbol, 'buy')
                        t_rate = b_rate = order['rate']     # 直近の買いレート
                    #
                    if c_rate >= t_rate:
                        if count == 0  and t_rate > l_rate:
                            # 目標レートを超えた
                            if signe['histgram'] > 0:
                                self.print_signal(signe, hist)
                                #
                                countA = 1
                                hist = 0.0
                                cont = 0
                                break
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
                                ret = True      # 「売り」の実行トリガー 
                            break
                    elif count == 1:
                        # 目標レートを下回った
                        countA = 0
                        break
            # read next record
            rs = self.cur.fetchone()
        #
        if countA != count or ( ('DX' in method) and count == 1 ):
            print_text = f"   >sell({symbol}):{ret}:{count}->{countA}:seq={seqnum}:"\
                       + f"{method}({b_rate:,.3f}):t_rate={t_rate:13,.3f}:"
            print(print_text + self.edit_cont_text(cont) + colored_reset())

            # update the control parmeter-count 
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"update trigger set count={countA},"\
                + f"histgram={hist},continuing={cont},updated_at='{timestamp}'"\
                + f" where seqnum={seqnum}"
            self.cur.execute(sql)
            self.conn.commit()
        #
        return ret
#     
    def check_buy_tradeRate(self, symbol, c_rate, l_rate):
        self.to_exchange = None
        self.exec_amount = None
        self.exec_type = None

        sql = "select * from trigger where "\
            + f"trade='buy' and symbol='{symbol}' and count <> 2"        
        rs = self.cur.execute(sql).fetchone()
        #
        ret = False
        count = countA = 0
        method = ''
        b_rate = 0.0
        #
        while rs != None:
            if rs['exchange'] != '*' :
                seqnum = rs['seqnum']
                b_rate = t_rate = rs['rate']
                countA = count = rs['count']
                hist = rs['histgram']
                cont = rs['continuing']
                method = rs['method'].upper()
                #print(f"buy :{t_rate}:{method}:{l_rate} -> {c_rate}")

                self.to_exchange = rs['exchange']
                self.exec_amount = rs['amount']
                self.exec_type = rs['exectype']
                #
                if 'IM' in method:
                    if c_rate <= t_rate and t_rate < l_rate:
                        # 目標レートを下回った
                        countA = 2
                        ret = True
                        break
                elif 'GX' in method:
                    # 統計値の取得
                    signe = self.get_macd_signe(symbol)
                    if 'SIG' in method:
                        # 目標レートの設定
                        t_rate = self.get_targetRate('buy', method, signe['lower'], signe['std'])
                        if b_rate != 0.0 and b_rate < t_rate:
                            t_rate = b_rate
                    elif b_rate == 0.0:                     
                        order = self.get_lastOrder(self.to_exchange, symbol, 'sell')
                        t_rate = b_rate = order['rate']     # 直近の売りレート
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
                                break
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
                                ret = True      # 「買い」の実行トリガー 
                            break
                    elif count == 1:
                        # 目標レートを超えた
                        countA = 0
                        break
                #
            # read next record
            rs = self.cur.fetchone()
        #
        if countA != count or ( ('GX' in method) and count == 1 ):
            print_text = f"   >buy({symbol}):{ret}:{count}->{countA}:seq={seqnum}:"\
                       + f"{method}({b_rate:,.3f}):t_rate={t_rate:13,.3f}:"
            print(print_text + self.edit_cont_text(cont) + colored_reset())

            # update the control parmeter-count 
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"update trigger set count={countA},"\
                + f"histgram={hist},continuing={cont},updated_at='{timestamp}'"\
                + f" where seqnum={seqnum}"
            self.cur.execute(sql)
            self.conn.commit()
        #
        return ret
#
    def pandas_read_ratelogs(self, params):
        if params['sym'] == '*':
            sql ="select * from ratelogs"
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
#eof
