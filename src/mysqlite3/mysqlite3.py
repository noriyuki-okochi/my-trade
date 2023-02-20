#
#
# Class for sqlite3
#     
#import sys
import sqlite3
import pandas
#import os
#from math import sqrt
#import json
import time
from datetime import datetime
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

    def rollback(self):
        self.conn.rollback()
    def commit(self):
        self.conn.commit()

    def execute(self, sql):
        return self.cur.execute(sql)
    def update_balance(self, exchange, symbol, amount,rate):
        sql = "select * from balance where "\
            + f"exchange='{exchange}' and symbol='{symbol}'"
        rs = self.cur.execute(sql).fetchone()
        if rs == None:
            sql = "insert into balance(exchange,symbol,amount,rate) values("\
                + f"'{exchange}',"\
                + f"'{symbol}',"\
                + f"{amount},"\
                + f"{rate})"
            self.cur.execute(sql)
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = "update balance set "\
                + f"amount={amount},rate={rate},"\
                + f"updated_at='{timestamp}'"\
                + f" where exchange='{exchange}' and symbol='{symbol}'"
            self.cur.execute(sql)
        self.conn.commit()

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

    def insert_trigger(self, symbol, trade, ratelist):
        # delete old datas
        sql = "delete from trigger where "\
            + f"symbol='{symbol}' and trade='{trade}'"
        self.cur.execute(sql)
        # insert new datas
        for rate in ratelist:
            if rate[:1].isdigit() == True:
                exchange = None
                if rate.find(':') != -1:
                    exchange = rate[rate.find(':')+1:]
                    rate = rate[:rate.find(':')]
                    sql = "insert into trigger(symbol,trade,rate,exectype,exchange)"
                else:
                    sql = "insert into trigger(symbol,trade,rate,exectype)"
                if rate[0] == '-':
                    exectype = 'STOP'
                    rate = rate[1:]
                else:
                    exectype = 'LIMIT'
                #
                sql += f" values('{symbol}','{trade}',{rate},'{exectype}'"
                if exchange != None:
                    sql += f",'{exchange}'"
                sql += ")"
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
    
    def check_tradeRate(self, trade, symbol, c_rate, l_rate):
        ret = False
        self.to_exchange = None
        sql = "select * from trigger where "\
            + f"trade='{trade}' and symbol='{symbol}' and count=0 and "
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
            if rs['exchange'] != None:
                self.to_exchange = rs['exchange']
            self.exec_type = rs['exectype']
            count = rs['count'] + 1
            seqnum = rs['seqnum']
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"update trigger set count={count},updated_at='{timestamp}'"\
                + f" where seqnum={seqnum}"
            self.cur.execute(sql)
            self.conn.commit()
            ret = True
        return ret

    def toExchange(self):
        return self.to_exchange

    def execType(self):
        return self.exec_type

    def insert_orders(self, id, exchange, pair, trade, type, rate, amount):
        # insert new datas
        sql = "insert into orders(id, exchange, pair, order_side, order_type, rate, amount)"
        #
        sql += f" values({id},'{exchange}','{pair}','{trade}','{type}',{rate},{amount})"
        print(sql)
        self.cur.execute(sql)
        #
        self.conn.commit()

    def close(self):
        self.conn.close()
#
    def pandas_read_ratelogs(self, params):
        if params['sym'] == '*':
            sql ="select * from ratelogs"
        else:
            sql ="select * from ratelogs where symbol = :sym"
        if params['limit'] > 0:
            sql += " LIMIT :limit"
#        return pandas.read_sql_query(sql, con=self.conn, params=params)
        return pandas.read_sql_query(sql, con=self.conn, index_col='inserted_at',\
                                     parse_dates=('inserted_at'), params=params)
#eof
