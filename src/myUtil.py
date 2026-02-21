#
"""
"""
# appUtil
#     
import os
import sys
import pandas as pd
from datetime import datetime

#
# local package
from  env import * 
from  mysqlite3.mysqlite3 import MyDb
#
Commands_d = { '-import': ['history', 'account'],
               '-calc': ['account'],
               '-create': ['account', 'candle'],
               '-print': ['history','account'],
               '-delete': ['history','account','candle']
            }
Options_d = { '-ex': ['COINCHECK', 'GMOCOIN'],
              '-sym': ['BTC', 'ETH', 'IOST', 'FPL'],
              '-year': None
            }
Account_data_d = dict(account_year= [2025],
                        symbol= [''],  
                        exchange= [''],
                        buy_amount= [0.00],
                        buy_jpy = [0],
                        sell_amount= [0.00],
                        sell_jpy= [0],
                        receipt_amount= [0.00],
                        receipt_jpy= [0],
                        send_amount= [0.00],
                        send_jpy= [0],
                        f_carry_amount= [0.00],
                        f_carry_jpy= [0],
                        e_carry_amount= [0.00],
                        e_carry_jpy= [0],
                        average_unit= [0],
                        sale_proceeds= [0],
                        sale_costs= [0],
                        fee= [0],
                        income= [0],
                        note= ['備考']
                    )      
Delete_table_d = dict(history_coincheck= 'coincheck_trade_history',
                   history_gmocoin= 'gmocoin_trade_history',
                   candle= 'candlelogs',
                   account= 'account_statement'
                   ) 
# ヘルプ表示関数
def help():
    print(" --- command ---")
    print(" python ./src/myUtil.py {-import <import_t>|-print <print_t>|-create <create_t>|-calc <calc_t>|-delete <delete_t>|-help}\n"\
          "                         [-ex <exchange>] [-sym <symbol>] [-year <account_year>]")
    print(" --- Option ---")
    print(" <import_t> :: history|account")
    print(" <print_t>  :: history|account")
    print(" <create_t> :: account|candle")
    print(" <calc_t>   :: account")
    print(" <delete_t> :: history|candle|account")
    print(" <exchange> :: coincheck|gmocoin")
    print(" <symbol>   :: BTC|ETH|IOST|FPL")
    print(" <account_year> :: 2022|2023|2024|...")
# コマンドラインオプションのチェック関数
# args: コマンドライン引数リスト    
# opts: オプション文字列
# pos: オプション位置
# optname: オプション名
def check_options(args:list[str], optstr:str, pos:int, optname:str):
    optValue = None 
    if len(args) > (pos + 1) and args[pos + 1][0] != '-' : 
        if Options_d[optstr] == None:
            optValue = args[pos +1] 
        elif args[pos + 1].upper() in Options_d[optstr]:
            optValue = args[pos +1]
        else:
            print(f"{optname}は{Options_d[optstr]}のいずれかを指定してください。")
    else:
        print(f"{optname}を指定してください。")
    return optValue
# コマンドラインコマンドのチェック関数
# args: コマンドライン引数リスト    
# cmdstr: コマンド文字列
# pos: コマンド位置
# cmdname: コマンド名
def check_commands(args:list[str], cmdstr:str, pos:int, cmdname:str):
    print(f"check_commands:args={args}, cmdstr={cmdstr}, pos={pos}")
    cmdKind = None 
    if len(args) > (pos + 1) and args[pos + 1][0] != '-' : 
        if args[pos + 1].lower() in Commands_d[cmdstr]:
            cmdKind = args[pos +1]
        else:
            print(f"{cmdname}種別には{Commands_d[cmdstr]}のいずれかを指定してください。")
    else:
        print(f"{cmdname}種別を指定してください。")
    return cmdKind
#
# CSVデータのインポート関数
# 取引所からダウンロードした年間の取引履歴のCSVファイルをDBに登録する。
#  coincheck:coin_trade_history.csv
#  gmocoin  :gmo_trading_report.csv
# db: MyDbデータベースオブジェクト
# exchange: 取引所
# 戻り値: 成功=True, 失敗=False
#
def import_trade_history(db:MyDb, exchange:str):
    if exchange == 'coincheck':
        csvfile = '../coin_trade_history.csv'
        table_name = 'coincheck_trade_history'
    elif exchange == 'gmocoin':
        csvfile = '../gmo_trading_report.csv'
        table_name = 'gmocoin_trade_history'
    else:
        print(f"[import_trade_history]error: exchange '{exchange}' not supported.")
        return False
    
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_trade_history]error: csv-file({csvfile}) not found.")
        return False    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_trade_history]:read_csv:{df.shape}")
    
    #取引日時のフォーマット変換（'2023/1/1 12:00' -> '2023-01-01 12:00' ）
    for i in  range(df.shape[0]):
        date_time:list = df.iat[i, 0].split(' ')      # 2023/1/1 12:00
        ymd:list = date_time[0].split('/')            # 2023/1/1
        df.iat[i, 0] = f"{ymd[0]}-{int(ymd[1]):02}-{int(ymd[2]):02} {date_time[1]}"
    # DBへ履歴データ登録
    #db.delete_tracking_data()      # 登録済データの削除
    df.to_sql(table_name, db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_trade_history]info:import '{csvfile}' to {table_name}:{df.shape}.")
    return True
#
# CSVデータのインポート関数
# db: MyDbデータベースオブジェクト
# csvfile: CSVファイルパス
# table_name: 登録テーブル名
# 戻り値: 成功=True, 失敗=False
def import_csv2db(db:MyDb, 
                  csvfile = '../account_statement.csv',
                  table_name = 'account_statement'):
    #
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_csv2db]error: csv-file({csvfile}) not found.")
        return False    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_csv2db]:read_csv:{df.shape}")
    
    # DBへ履歴データ登録
    #db.delete_tracking_data()      # 登録済データの削除
    df.to_sql(table_name, db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_csv2db]info:import '{csvfile}' to {table_name}:{df.shape}.")
    return True
#
# 取引の集計関数（Coincheck用）
# db: MyDbデータベースオブジェクト
# key_t: (exchange, symbol, year)
# 戻り値: 集計データ辞書
def agregate_trade_coin(db:MyDb, key_t:tuple):
    exchange, symbol, year = key_t
    symbol = symbol.upper()
    print(f"年度：{year},取引所：'{exchange.upper()},通貨：{symbol}'の取引を集計します。")
    
    data_d = dict.fromkeys(Account_data_d.keys(), 0.0)              
    data_d['account_year'] = year   
    data_d['symbol'] = symbol   
    data_d['exchange'] = exchange
    
    sales_df: pd = db.agregate_trade_sales(exchange)
    if  not sales_df.empty:
        sales_df = sales_df.fillna(0)
        print(f"=== {exchange} sales history ===")
        print(sales_df)
        fee:int = 0
        #
        # 購入取引データ
        t_df = sales_df[ (sales_df['symbol'].str.contains(symbol)) & (sales_df['side'] == '購入') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['buy_amount'] = t_df.at[idx[0], 'in_amount']
            data_d['buy_jpy'] = int(t_df.at[idx[0], 'out_amount'])
            if t_df['fee'] is not None: fee += t_df.at[idx[0], 'fee']
        # 売却取引データ
        t_df = sales_df[ (sales_df['symbol'].str.contains(symbol)) & (sales_df['side'] == '売却') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['sell_amount'] = t_df.at[idx[0], 'out_amount']
            data_d['sell_jpy'] = int(t_df.at[idx[0], 'in_amount'])
            if t_df['fee'] is not None: fee += t_df.at[idx[0], 'fee']
        data_d['fee'] = int(fee)
    
    #  otheres_history.
    others_df: pd = db.agregate_trade_otheres(exchange)
    if  not others_df.empty:
        others_df = others_df.fillna(0)
        print(f"=== {exchange} otheres history ===")
        print(others_df)
        # 受取取引データ（ステーキング、エアドロップ等）
        t_df = others_df[ (others_df['symbol'] == symbol) & (others_df['side'] == '受取') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['receipt_amount'] = t_df.at[idx[0], 'in_amount']
            data_d['receipt_jpy'] = int(db.calc_otheres_jpy(exchange, symbol, '受取'))
    #
    return data_d
#
# 取引の集計関数（GMOコイン用）
# db: MyDbデータベースオブジェクト  
# key_t: (exchange, symbol, year)
# 戻り値: 集計データ辞書
def agregate_trade_gmo(db:MyDb, key_t:tuple):
    exchange, symbol, year = key_t
    symbol = symbol.upper()
    print(f"取引所：'{exchange.upper()},通貨：{symbol}'の取引を集計します。")
    
    data_d = dict.fromkeys(Account_data_d.keys(), 0.0)              
    data_d['account_year'] = year   
    data_d['symbol'] = symbol   
    data_d['exchange'] = exchange

    sales_df: pd = db.agregate_trade_sales(exchange)
    if  not sales_df.empty:
        sales_df = sales_df.fillna(0)
        print(f"=== {exchange} sales history ===")
        print(sales_df)
        fee = 0
        #
        # 購入取引データ
        t_df = sales_df[ (sales_df['symbol'] == symbol) & (sales_df['side'] == '買') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['buy_amount'] = t_df.at[idx[0], 'amount']
            data_d['buy_jpy'] = int(t_df.at[idx[0], 'jpy'])
            fee += t_df.at[idx[0], 'fee']
        # 売却取引データ
        t_df = sales_df[ (sales_df['symbol'] == symbol) & (sales_df['side'] == '売') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['sell_amount'] = t_df.at[idx[0], 'amount']
            data_d['sell_jpy'] = int(t_df.at[idx[0], 'jpy'])
            fee += t_df.at[idx[0], 'fee']

        return_df: pd = db.gmo_return_fee()
        if  not return_df.empty:
            return_df = return_df.fillna(0)
            print(f"=== {exchange} return history ===")
            print(return_df)
            # 手数料返還取引データ
            t_df = return_df[ (return_df['symbol'] == symbol) & (return_df['精算区分'].str.contains('手数料返金')) ]
            if not t_df.empty :
                #print(t_df)
                idx = t_df.index
                fee -= t_df.at[idx[0], 'jpy']
        data_d['fee'] = int(fee)
    
    #  otheres_history.
    others_df: pd = db.agregate_trade_otheres(exchange)
    if  not others_df.empty:
        others_df = others_df.fillna(0)
        print(f"=== {exchange} otheres history ===")
        print(others_df)
        # 預入取引データ（ステーキング、エアドロップ等）
        t_df = others_df[ (others_df['symbol'] == symbol) & (others_df['side'] == '預入') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['receipt_amount'] = t_df.at[idx[0], 'amount']
            data_d['receipt_jpy'] = int(db.calc_otheres_jpy(exchange, symbol, '預入'))
        # 送付取引データ（手数料等）
        t_df = others_df[ (others_df['symbol'] == symbol) & (others_df['side'] == '送付') ]
        if not t_df.empty :
            #print(t_df)
            idx = t_df.index
            data_d['send_amount'] = t_df.at[idx[0], 'amount']
            data_d['send_jpy'] = int(db.calc_otheres_jpy(exchange, symbol, '送付'))
    #    
    return data_d
#
# 所得金額を計算する
#
def calc_account_statement(data_d:dict):
    # 購入
    buy_amt = data_d['buy_amount'] + data_d['receipt_amount']
    buy_jpy = data_d['buy_jpy'] + data_d['receipt_jpy']
    # 総平均単価
    amt = data_d['f_carry_amount'] + buy_amt
    jpy = data_d['f_carry_jpy'] + buy_jpy
    ave = (jpy/amt) if amt != 0 else 0
    data_d['average_unit'] = ave
    # 売却原価
    sell_proc_amt = data_d['sell_amount'] + data_d['send_amount']
    sell_proc_jpy = int(sell_proc_amt * ave)
    # 繰越金額計算
    e_carry_amt = data_d['f_carry_amount'] + buy_amt - sell_proc_amt
    data_d['e_carry_amount'] = e_carry_amt
    data_d['e_carry_jpy'] = int(e_carry_amt * ave)
    #
    # 売却価格（収入金額）
    sale_proceeds = data_d['sell_jpy'] + data_d['send_jpy']     
    data_d['sale_proceeds'] = sale_proceeds
    # 売却原価
    sale_costs = sell_proc_jpy                          
    data_d['sale_costs'] = sale_costs
    # 手数料
    fee = data_d['fee']
    # 売却益計算（所得金額）
    income = sale_proceeds - sale_costs - fee
    data_d['income'] = income

    return data_d
#
#
# メイン関数
def main():
    # DB接続
    db = MyDb(DB_PATH, True)
    #
    # オプション引数のチェック
    #
    args = sys.argv
    opts_d = {opt: idx for idx, opt in enumerate(args) if opt.startswith('-')}
    print(f"opts_d:{opts_d}")
    # ヘルプ表示
    if '-help' in opts_d:
        help()
        return
    if '-test' in opts_d:
        last_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"last_date:{last_date}")
        db.insert_candlelogs('BTC', last_date)
        return    
    # 取引所
    exchange = None
    if '-ex' in opts_d:
        exchange = check_options(args, '-ex', opts_d['-ex'], "取引所")
        if exchange is None: return
        exchange = exchange.lower()
    # 通貨名
    symbol = None
    if '-sym' in opts_d:
        symbol = check_options(args, '-sym', opts_d['-sym'], "通貨名")
        if symbol is None: return
        symbol = symbol.upper()
    # 年度
    year = datetime.now().year - 1      # デフォルトは前年
    if '-year' in opts_d:
        year = check_options(args, '-year', opts_d['-year'], "年度")
        if year is None: return          
        year = int(year)
    #
    # コマンド引数のチェック、実行
    #
    if '-import' in opts_d:
        # CSVデータのインポート（DB登録）
        import_kind = check_commands(args, '-import', opts_d['-import'], "インポート")
        if import_kind is None: return
        if import_kind == 'account':
            # 暗号通貨の取引計算書（確定申告用）
            # デフォルト
            # csvfile = '../account_statement.csv',
            # table_name = 'account_statement'):
            import_csv2db(db)
            db.close()
        elif import_kind == 'history':
            # import the trade_history.
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -import history -ex <exchange>")
                return
            print(f"取引所：'{exchange.upper()}'の取引履歴をインポートします。")
            if db.delete_trade_history(exchange) == True:
                import_trade_history(db, exchange)
            db.close()
    if '-calc' in opts_d:
        # 登録データの集計
        calc_kind = check_commands(args, '-calc', opts_d['-calc'], "集計")
        if calc_kind is None: return
        if calc_kind == 'account':
            # 暗号通貨の取引計算書（確定申告用）の集計
            if symbol is None: 
                print("通貨名を指定してください。")
                print("usage: myUtil.py -calc account -ex <exchange> -sym <symbol>")
                return
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -calc account -ex <exchange> -sym <symbol>")
                return
            # 取引所の取引履歴テーブルからデータの取得・集積
            key_t = (exchange, symbol, year)
            if exchange == 'coincheck':
                data_d = agregate_trade_coin(db, key_t)
            elif exchange == 'gmocoin':
                data_d = agregate_trade_gmo(db, key_t) 
                       
            if data_d is not None:
                # 前年度繰越金を繰り入れ
                account_df: pd = db.pandas_read_account( (exchange, symbol, year - 1) )
                if  not account_df.empty:
                    data_d['f_carry_amount'] = account_df.iat[0, 13]    #'e_carry_amount'
                    data_d['f_carry_jpy'] = account_df.iat[0, 14]       #'e_carry_jpy')
                print(f">> {exchange} account statement({symbol}:{year}) aggregated.")
                # 所得金額の計算
                data_d = calc_account_statement(data_d)
                print(f">> {exchange} account statement({symbol}:{year}) calculated.")
                data_d['note'] = f"{year}:{symbol}:{exchange}"
                print(data_d)
                # 計算結果でDBのレコード更新
                db.update_account_statement(key_t, data_d)
                # CSVファイル作成
                df = pd.DataFrame(data_d, index=['no'])
                out_csv = f"../{year}_{symbol.lower()}_{exchange}_account_statement.csv"
                df.to_csv(out_csv, mode='w', float_format='%.4f', na_rep='NaN', sep=',', index=False)
                print(f"{out_csv} created.")

    #
    if '-print' in opts_d:
        # 登録データの表示
        prt_kind = check_commands(args, '-print', opts_d['-print'], "表示")
        if prt_kind is None: return
        if prt_kind == 'history':
            # 取引所の取引履歴
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -print history -ex <exchange>")
                return
            # agregate the trade_history.
            print(f"取引所：'{exchange.upper()}'の取引履歴を集計します。")              
            #  sales_history.
            sales_df: pd = db.agregate_trade_sales(exchange)
            if  sales_df is not None:
                print(f"=== {exchange} sales history ===")
                print(sales_df)
            if  exchange == 'gmocoin':
                #  purchase_history.
                print(f"=== {exchange} return history ===")
                return_df: pd = db.gmo_return_fee()
                if  return_df is not None:
                    print(return_df)
                
            #  otheres_history.
            others_df: pd = db.agregate_trade_otheres(exchange)
            if  others_df is not None:
                print(f"=== {exchange} otheres history ===")
                print(others_df)
                
        elif prt_kind == 'account':
            # 暗号通貨の取引計算書（確定申告用）
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -print account -ex <exchange> -sym <symbol>")
                return
            if symbol is None: 
                print("通貨名を指定してください。")
                print("usage: myUtil.py -print account -ex <exchange> -sym <symbol>")
                return

            key_t = (exchange, symbol, year)
            account_df: pd = db.pandas_read_account( key_t )
            if  not account_df.empty: 
                print(f">> {exchange} account statement({symbol}:{year})")
                print(account_df)
            else:
                print(f">> {exchange} account statement({symbol}:{year}) is empty.")
#
    if '-create' in opts_d:
        # 登録データの初期作成
        crt_kind = check_commands(args, '-create', opts_d['-create'], "作成")
        if crt_kind is None: return
        if crt_kind == 'account':
            # 暗号通貨の取引計算書（確定申告用）
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -create account -ex <exchange> -sym <symbol>")
                return
            if symbol is None: 
                print("通貨名を指定してください。")
                print("usage: myUtil.py -create account -ex <exchange> -sym <symbol>")
                return
            
            #　初期データのDataFrameを作成
            data_d = Account_data_d.copy()
            data_d['account_year']= [year]
            data_d['symbol']= [symbol]  
            data_d['exchange']= [exchange]
            ini_df = pd.DataFrame(data_d)
            # 前年の繰越金額を取得
            key_t = (exchange, symbol, year - 1)
            account_df: pd = db.pandas_read_account( key_t )
            if  not account_df.empty:
                # 初期データの行を追加
                account_df = pd.concat( [account_df, ini_df], ignore_index=True)
                # 今年のアカウントステートメントを作成するために、前年の繰越金額を初期データにセットする。
                e_amt = account_df.iat[0, 13]       #'e_carry_amount'
                e_jpy = account_df.iat[0, 14]       #'e_carry_jpy')
                account_df.iat[1, 11] = e_amt       #'f_carry_amount'
                account_df.iat[1, 12] = e_jpy       #'f_carry_jpy'
                #print(account_df)
                # 今年のアカウントステートメントを作成する。
                account_df.drop(0, inplace=True, errors='ignore')
            else:
                # 初期データの行を追加
                account_df = pd.concat( [account_df, ini_df], ignore_index=True)
            # DBへ登録
            account_df['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            account_df.to_sql('account_statement', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
            print(f">> {exchange} account statement({symbol}:{year}) created.") 

        elif crt_kind == 'candle':
            # 自動取引用ローソク足データ登録
            if symbol is None: 
                print("通貨名を指定してください。")
                print("usage: myUtil.py -create candle -sym <symbol>")
                return
            print(f"ローソク足履歴データを登録します。")              
            inserted_count = db.insert_candlelogs(symbol)
            print(f">> {inserted_count} rows inserted.")                  

    if '-delete' in opts_d:
        # レコード削除
        del_kind = check_commands(args, '-delete', opts_d['-delete'], "削除")
        if del_kind is None: return
        if del_kind == 'candlelogs':
            exchange = None 
        #
        if del_kind == 'history': 
            if exchange is None: 
                print("取引所を指定してください。")
                print("usage: myUtil.py -delete history -ex <exchange> -sym <symbol>")
                return
            del_kind = f"history_{exchange}"
            exchange = None            
        target = Delete_table_d[del_kind]
        
        yy = year if year is not None else '*'
        ex = exchange if exchange is not None else '*'
        sym = symbol if symbol is not None else '*'
        key_t = (yy, ex, sym)
        print(f"Target-table:{target}, key:{key_t}. Are you sure?[y/n].")
        ans = input('>')
        if ans == 'y':
            db.delete_trade_accounts_records(target, key_t)
#
if __name__ == "__main__":
    print(os.getcwd())
    main()
    #
#eof
