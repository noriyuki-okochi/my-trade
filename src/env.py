import os

##############################
# 共通定数
##############################
ACCESS_KEY_CHECK = '9JwEAisq2xCWssRk'
SECRET_KEY_CHECK = 'O7gSYjrcO_flbga19uk01ZR4jZ3Iy5u7'
ACCESS_KEY_GMO = 'OTltuobtT1Xgd91Uxm8O20EN9w/x/6AX'
SECRET_KEY_GMO = 'F+HWh1itXkwJRxPuprwl0ZTXPQRYVZZDHzSPk8i2Brm9Mp1bovo7FNJXEuFK2rQY'
DB_PATH = "../Auto-trade.db"
EXCHANGE_CHECK = 'coincheck'
EXCHANGE_GMO = 'gmocoin'
SYM_BTC = 'btc'
SYM_ETH = 'eth'
SYM_MATIC = 'matic'
SYM_IOST = 'iost'
TRADE_SELL = 'sell'
TRADE_BUY = 'buy'
# 計測間隔
#INTERVAL = int(os.environ['INTERVAL'])
INTERVAL = (60*4)       # 4Min.
MAX_LINES = 15           # 4Min x 15 = 60Min = 1.0H
#レートデータ保存期間
#RATELOGS_DAYS = 180      # 180days
RATELOGS_DAYS = None

#直近成約売買表示日数
recently_order = os.getenv('RECENTLY_ORDER')
if recently_order != None:
    recently_order = int(recently_order)
else:
    recently_order = 10

SLEEP_DAYS = os.getenv('SLEEP_DAYS')
#print(SLEEP_DAYS)
if SLEEP_DAYS == None:
    SLEEP_DAYS = 1
sleep_time = (60*60*24)*float(SLEEP_DAYS)
#
#過去サンプリングログの削除
delval = os.getenv('DEL_SPAN_VALUE')
if delval != None:
    delval = int(delval)
else:
    delval = 1
delopt = os.getenv('DEL_SPAN_OPT')
if delopt == None:
    delopt = 'y'
#
# チャート表示コイン
#
coin_sym = os.getenv('COIN_SYMBOLS')
if coin_sym != None:
    coin_symbols = tuple(coin_sym.split())
else:
    coin_symbols = ('btc',)

#
# 自動取引コイン
#
auto_coins = os.getenv('AUTO_COIN_SYMBOLS')
if auto_coins != None:
    auto_coin_symbols = auto_coins.split()
else:
    auto_coin_symbols = [SYM_BTC]

# 「売り」トリガー
sell_rate = { 'btc':os.getenv('BTC_SELL_RATE'),
              'eth':os.getenv('ETH_SELL_RATE'),
              'matic':os.getenv('MATIC_SELL_RATE'),
              'iost':os.getenv('IOST_SELL_RATE')}

# 「買い」トリガー
buy_rate = { 'btc':os.getenv('BTC_BUY_RATE'),
             'eth':os.getenv('ETH_BUY_RATE'),
             'matic':os.getenv('MATIC_BUY_RATE'),
             'iost':os.getenv('IOST_BUY_RATE')}
# 比較基準レート
std_rate = { 'btc':os.getenv('BTC_STD_RATE'),
             'eth':os.getenv('ETH_STD_RATE'),
             'matic':os.getenv('MATIC_STD_RATE'),
             'iost':os.getenv('IOST_STD_RATE')}

# チャート表示ターゲットレート
alart_rate = { 'btc':os.getenv('BTC_TARGET_RATE'),
               'eth':os.getenv('ETH_TARGET_RATE'),
               'matic':os.getenv('MATIC_TARGET_RATE'),
               'iost':os.getenv('IOST_TARGET_RATE')}
# スプレッド中央値（購入）レート
base_rate = { 'btc':os.getenv('BTC_BASE_RATE'),
              'eth':os.getenv('ETH_BASE_RATE'),
              'matic':os.getenv('MATIC_BASE_RATE'),
              'iost':os.getenv('IOST_BASE_RATE')}
# スプレッド（％）
sp_rate = { 'btc':os.getenv('BTC_SP_RATE'),
            'eth':os.getenv('ETH_SP_RATE'),
            'matic':os.getenv('MATIC_SP_RATE'),
            'iost':os.getenv('IOST_SP_RATE')}
#
target_rate = {'btc':[],'eth':[],'matic':[],'iost':[]}
for sym in coin_symbols:
    #下限値
    if base_rate[sym] != None and sp_rate[sym] != None:
        lower_rate = float(base_rate[sym])*(1.0 - float(sp_rate[sym]))
        target_rate[sym].append(f"{lower_rate:.3f}:buy")
    #警報通知レート
    if target_rate[sym] != None:
        target_rate[sym] += alart_rate[sym].split()
    #上限値
    if base_rate[sym] != None and sp_rate[sym] != None:
        upper_rate = float(base_rate[sym])*(1.0 + float(sp_rate[sym]))
        target_rate[sym].append(f"{upper_rate:.3f}:sell")
    #print(f"{sym}:{target_rate[sym]}")

# 警告（ブリンク）表示閾値（変動率）
blink_rate = os.getenv('BLINK_RATE')
if blink_rate == None:
    blink_rate = 1.0
else:
    blink_rate = float(blink_rate)
# 警告（メール送信）表示閾値（変動率）
mail_rate = os.getenv('MAIL_RATE')
if mail_rate == None:
    mail_rate = 3.0
else:
    mail_rate = float(mail_rate)
#
hist_continuing = os.getenv('HIST_CONTINUING')
if hist_continuing == None:
    hist_continuing = 4
else:
    hist_continuing = int(hist_continuing)

# 注文ID
#order_id = None
# 購入金額
order_amount_jpy: int = os.getenv('ORDER_AMOUNT_JPY')
if order_amount_jpy == None:
    order_amount_jpy = 2000
else:
    order_amount_jpy = int(order_amount_jpy)

    
print(f"mail:{mail_rate}%, blink:{blink_rate}%")
print(f"std_rate:{std_rate}")
print(f"spd_rate:{sp_rate}")

# 利益
#PROFIT = os.getenv('PROFIT')
#profit = float(PROFIT if type(PROFIT) is str and PROFIT != '' else 0.0)



# 通貨
#COIN = os.environ['COIN']
#PAIR = COIN + '_jpy'
# アルゴリズム
#ALGORITHM = os.environ['ALGORITHM']
# 購入金額
#AMOUNT = os.getenv('AMOUNT')

# シミュレーションモード
#SIMULATION = os.getenv('SIMULATION')
#simulation = False if SIMULATION is None or SIMULATION == '' or SIMULATION == 'false' else True
#
# テキスト属性
#
STYLE_NON = '0'
STYLE_BOLD = '1'
STYLE_LIGHT = '2'
STYLE_ITALIC = '3'
STYLE_UNDER = '4'
STYLE_BLINK = '5'
FG_BLACK = '30'
FG_RED = '31'
FG_GREEN = '32'
FG_YELLOW = '33'
FG_BLUE = '34'
FG_PURPLE = '35'
FG_CYAN = '36'
FG_WHITE = '3f'
BG_BLACK = '40'
BG_RED = '41'
BG_GREEN = '42'
BG_YELLOW = '43'
BG_BLUE = '44'
BG_PURPLE = '45'
BG_CYAN = '46'
BG_WHITE = '4f'
# eof
