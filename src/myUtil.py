#
"""
"""
# appUtil
#     
import os
import pandas as pd
import math

#
# local package
from  env import * 
from  mysqlite3.mysqlite3 import MyDb
#

#
# CSVデータのインポート関数
# db: MyDbデータベースオブジェクト
# cmds: コマンドライン引数リスト
# case_name: ケース名   
# 戻り値: 成功=True, 失敗=False
#
def import_trade_history(db:MyDb):
    #csvfile = '../gmo_2025_trading_report.csv'
    csvfile = '../coin_trade_history_20250101-20251231.csv'
    
    if csvfile == '' or os.path.isfile(csvfile) == False:
        # ファイルが存在しないとき終了
        print(f"[import_trade_history]error: csv-file({csvfile}) not found.")
        return False    
    # CSVファイルを読み込む
    df = pd.read_csv(csvfile)
    print(f"[import_trade_history]:read_csv:{df.shape}")
    
    # DBへトラッキングデータ登録
    #db.delete_tracking_data()      # 登録済データの削除
    df.to_sql('coincheck_trade_history', db.conn, if_exists='append', index=None, method='multi', chunksize=1024)
    print(f"[import_trade_history]info:import '{csvfile}' to 'trade_history'{df.shape}.")
    return True
#
# 登録ケースの削除関数
# db: MyDbデータベースオブジェクト
# case_name: 削除ケース名 
def delete_frame_info(db:MyDb, case_name):
    _,csvfile = db.get_file_path(case_name)
    if csvfile is not None:
        if db.delete_case(case_name) == True:
            print(f"[delete_frame_info]:info: case_name='{case_name}' deleted.")
            rcnt = db.delete_case_records('tracking_data', case_name)
            print(f"[delete_frame_info]:info: {rcnt} records deleted from tracking_data.")
            rcnt = db.delete_case_records('kyudo_data', case_name)
            print(f"[delete_frame_info]:info: {rcnt} records deleted from kyudo_data.")
        #
        print(f"> '{csvfile}' will be deleted. continue?. [y/n].")
        ans = input('>>')
        if ans == 'y': 
            try:
                os.remove( csvfile )
                print(f"[delete_frame_info]:info: '{csvfile}' deleted.")
                csvfile = csvfile.replace('track', 'kyudo')
                os.remove( csvfile )
                print(f"[delete_frame_info]:info: '{csvfile}' deleted.")
            except:
                print(f"[delete_frame_info]:info: '{csvfile}' not found.")
    
    else:
        print(f"[delete_frame_info]:error: case_name='{case_name}' not found.")
    return            
#
# 登録ケース名の変更関数
# db: MyDbデータベースオブジェクト
# from_name: 変更前ケース名 
# to_name: 変更後ケース名
def rename_frame_info(db:MyDb, from_name, to_name):
    fps,_ = db.get_fps(from_name)
    if fps is None:
        print(f"[rename_frame_info]:error: case_name='{from_name}' not found.")
    else:
        tables = [ 'tracking_data', 'kyudo_data' , 'frame_info' ]
        for tbl in tables:
            rcnt = db.copy_case(tbl, from_name, to_name)
            if rcnt is None:
                # コピー対象ケース名が存在しないとき
                continue
            if rcnt < 0:
                # コピー件数不一致エラーのとき
                db.delete_case_records(tbl, to_name)    # 変更後ケース名の登録データを削除
                continue
            #
            i = db.delete_case_records(tbl, from_name)      # 変更前ケース名の登録データを削除
            #print(f"[rename_frame_info]:info: {tbl}:{rcnt} records  deleted. {from_name}.")
            print(f"[rename_frame_info]:info: {tbl}:{rcnt} records  renamed from {from_name} to {to_name}.")
        #
    return None            
#
if __name__ == "__main__":
    print(os.getcwd())
    #
    db = MyDb(DB_PATH, True)
    import_trade_history(db)
    
    db.close()
#eof
