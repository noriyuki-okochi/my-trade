#
"""
This script generates a candlestick chart with various technical indicators for cryptocurrency trading data.
It uses Plotly for visualization and reads data from a SQLite database.
Usage:
    chart.py {symbol1 [symbol2]|*} [display-days] [-past-days] [-m(acd)] 
             [-a(uto)] [-d(ebug)] [-b(ottom)] [-p(redict)[split-size]]
Arguments:
    symbol1, symbol2: Cryptocurrency symbols to display. Use '*' to display all available symbols.
    display-days: Number of days to display on the chart.
    -past-days: Number of past days to consider for the chart.
    -m: Display MACD (Moving Average Convergence Divergence) indicator.
    -a: Display auto-trade points.
    -d: Enable debug mode.
    -b: Position the legend at the bottom.
    -p: Enable prediction mode with optional split size for training/testing data.
Modules:
    - sys: Provides access to command-line arguments.
    - os: Provides a way of using operating system dependent functionality.
    - pandas: Data analysis and manipulation library.
    - plotly: Interactive graphing library.
    - env: Local module for environment variables.
    - myApi: Local module for API interactions.
    - mysqlite3.mysqlite3: Local module for SQLite database interactions.
    - mylearn.mylearn: Local module for machine learning operations.
Functions:
    - make_subplots: Creates a subplot grid for the chart.
    - add_trace: Adds a trace (data series) to the chart.
    - update_layout: Updates the layout of the chart.
    - update_traces: Updates the properties of traces in the chart.
    - write_html: Writes the chart to an HTML file and optionally opens it in a web browser.
Classes:
    - MyDb: Class for interacting with the SQLite database.
    - MyLearn: Class for machine learning operations.
Workflow:
    1. Parse command-line arguments.
    2. Connect to the SQLite database.
    3. Read and process rate data for the specified symbols.
    4. Generate technical indicators (SMA, EMA, MACD, etc.).
    5. Create subplots and add traces for each symbol.
    6. Optionally, perform machine learning predictions.
    7. Update the layout and properties of the chart.
    8. Write the chart to an HTML file and open it in a web browser.
"""
# chart main
#     
import sys
import os
# local
from env import *
from myApi import *
from mysqlite3.mysqlite3 import MyDb
import pandas as pd
#import numpy as np
import plotly.graph_objects as go
#import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from mylearn.mylearn import MyLearn

#print(http.__file__)
#
# start of main
#
print(os.getcwd())
# print command line(arguments)
#
# chart.py {symbol1 [symbol2]|*} [display-days] [-past-days] [-m(acd)] 
#          [-a(uto)] [-d(ebug)] [-b(ottom)] [-p(redict)[split-size]]
#
args = sys.argv
cmdline = ""
for arg in args:
    cmdline += f" {arg}"
# connect AUto-trade.db
db = MyDb(DB_PATH)
#print(db)
print('<< chart start >>')
print(cmdline)
#
verbose = False         # debug write
macd_flg = False        # not display MACD
auto_flg = False        # auto-trade point
predict_flg = False
split_size = None
#
last = (24*7*1)         # 24h*week-days*week(default is 1-week)
# 
selsyms = [sym for sym in args if sym in coin_symbols]
selnum = len(selsyms)
if selnum == 0:
    selsyms.append('*')         # all coins
    selnum = 4
#
nums = [int(num) for num in args if num.isnumeric()]
if len(nums) > 0:       # display days
    last = 24*nums[0]   #24h*days
#
#
opts = [opt for opt in args if opt.startswith('-')]
if '-m' in opts and selnum == 1:    #MASD
    macd_flg = True
#
autopt = [opt for opt in opts if opt.startswith('-a')]
if len(autopt) > 0:
    auto_flg = True
    auto_last = last
    if autopt[0][2:].isnumeric():
        auto_last = 24*int(autopt[0][2:])
#
optnums = [int(num[1:]) for num in opts if num[1:].isnumeric()]
if len(optnums) > 0:    # past days
    mlast = 24*optnums[0]
else:
    mlast = last
#
if '-b' in opts:        #yanchor
    legend_dict = dict(x=0.01,y=0.01,xanchor='left',yanchor='bottom',orientation='h')
else:
    legend_dict = dict(x=0.01,y=0.99,xanchor='left',yanchor='top',orientation='h')
#
if '-d' in opts:        #debug write
    print(selsyms)
    print(nums)
    print(opts)
    verbose = True
    
#predict by MyLearn
predopt = [opt for opt in opts if opt.startswith('-p')]
if len(predopt) > 0:
    predict_flg = True
    split_size = 0.5
    if predopt[0][2:].isnumeric():
        split_size = float(predopt[0][2:])
    #
    legend_dict = dict(x=0.01,y=0.99,xanchor='left',yanchor='top',orientation='h')
#
# define sub-plots block
#
if selsyms[0] == '*':
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.1,
                        x_title='Hour', y_title='Rate',
                        subplot_titles=[sym.upper() for sym in coin_symbols])
else:
    if macd_flg == True :
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                        subplot_titles=[selsyms[0].upper(),'MACD'],
                        shared_xaxes=True,
                        specs=[[{"secondary_y": False}], [{"secondary_y": True}]])
    elif predict_flg == True:
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                        subplot_titles=[selsyms[0].upper(),'Permutation Importance'])
    else:
        if selnum == 1:
            fig = make_subplots(rows=1, cols=1, 
                        subplot_titles=[selsyms[0].upper()])
        else:
            fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1,
                        subplot_titles=[sym.upper() for sym in selsyms if sym != ''])
if '-d' in opts:
    fig.print_grid()
#
limit = 0
icount = 1
for sym in coin_symbols:
    if selsyms[0] == '*' or sym in selsyms:
        if selsyms[0] == '*':
            irow = int((icount+1)/2)
            icol = int((icount+1)%2 + 1)
        else:
            irow = icount
            icol = 1
        #print(f"symbol:{sym}")
        #
        # read rate-data from db to pandas
        #
        print(f"{sym}:{target_rate[sym]}")
        params = {"sym":sym,"limit":limit}
        df = db.pandas_read_ratelogs(params)
        #print(df.index)
        #print(df.count())
        # convert to OHLC
        mdf = df['rate'].resample('H').ohlc()
        mdf.columns = ['Open', 'High', 'Low', 'Close']
        #d_all = pandas.date_range(start=mdf.index[0], end=mdf.index[-1], freq='H')
        #print(d_all) 
        #
        # fill Non data with left col
        mdfil = mdf.fillna(method = 'ffill',inplace = False)
        # SMA
        mdfil["sma5"] = mdfil["Close"].rolling(window=5).mean()
        mdfil["sma25"] = mdfil["Close"].rolling(window=25).mean()
        # STD
        mdfil["std"] = mdfil["Close"].rolling(window=25).std(ddof=1)
        # EMA
        mdfil["ema12"] = mdfil["Close"].ewm(span=12,adjust=False).mean()
        mdfil["ema26"] = mdfil["Close"].ewm(span=26,adjust=False).mean()
        # MACD,SIGNAL
        mdfil["macd"] = mdfil["ema12"] - mdfil["ema26"]
        mdfil["signal"] = mdfil["macd"].ewm(span=9,adjust=False).mean()
        # Volatility
        '''
        mdfil["max"] = mdfil["High"].rolling(window=prd_volat).max()
        mdfil["volat"] = mdfil["max"] - mdfil["Low"].rolling(window=prd_volat).min()
        mdfil["volat"] = mdfil["volat"] / mdfil["max"]
        '''
        mdfil["volat"] = mdfil["High"] - mdfil["Low"]
        mdfil["volat"] = mdfil["volat"] / mdfil["Open"]
        '''
        mdfil["volat"] = (mdfil["High"] - mdfil["Low"])/mdfil["Open"]
        mdfil["volsma"] = mdfil["volat"].rolling(window=prd_volat).mean()
        '''
        #
        # select diaplay datas
        #
        mdf = mdf.tail(mlast)
        mdfil = mdfil.tail(mlast)
        if mlast > last:
            mdf = mdf.head(last)
            mdfil = mdfil.head(last)
        #
        if predict_flg:
            #
            mlearn = MyLearn(mdfil)
            mlearn.tarin_test_split(split_size)
            pred_numpy = mlearn.execute()
            print(f"pred :\n {pred_numpy}")
            rslt = mlearn.show_explanation()
            #
            # create predict-data to plot
            #
            close_numpy = mdfil['Close'].to_numpy()
            close_numpy[:len(pred_numpy)] = None
            close_numpy[len(pred_numpy):] = pred_numpy
            print(f"close_nupmy = {len(close_numpy)}, pred_numpy = {len(pred_numpy)}")
            mdfil["predict"] = close_numpy
            #exit(0)
        #
        # create auto-trade rate-data
        #
        if auto_flg:
            df_tail = df.tail(1)        # get a record on last index 
            df_tail.iat[0,3] = None     # set rate's value to NaN
            if verbose:
                print(df_tail)
            # read auto-buy-trade-rate-data from db to pandas
            sym_side = sym + '_buy'
            params = {"sym":sym_side,"limit":limit}
            df_buy = db.pandas_read_ratelogs(params)
            buy_count =df_buy['rate'].count()
            print(f"buy_count : {buy_count}")
            if buy_count > 0:
                # append the last record in sampling rate's records
                df_buy = pd.concat([df_buy, df_tail])
                # resample and convert to the first rate-value
                mdf_buy = df_buy['rate'].resample('H').first()
                # select diaplay datas
                mdf_buy = mdf_buy.tail(auto_last)
                if verbose:
                    print(mdf_buy)
            #
            # read auto-sellbuy-trade-rate-data from db to pandas
            sym_side = sym + '_sell'
            params = {"sym":sym_side,"limit":limit}
            df_sell = db.pandas_read_ratelogs(params)
            sell_count =df_sell['rate'].count()
            print(f"sell_count: {sell_count}")
            if sell_count > 0:
                # append the last record in sampling rate's records
                df_sell = pd.concat([df_sell, df_tail])
                # resample and convert to the first rate-value
                mdf_sell = df_sell['rate'].resample('H').first()
                # select diaplay datas
                mdf_sell = mdf_sell.tail(auto_last)
                if verbose:
                    print(mdf_sell)
        #
        # < OHLC >
        fig = fig.add_trace( go.Candlestick(x=mdf.index,
                                        name="ohlc",
                                        open=mdf["Open"],
                                        high=mdf["High"],
                                        low=mdf["Low"],
                                        close=mdf["Close"]),
                            row = irow, 
                            col = icol  
                        )
        # < SMA5 >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="sma5",
                                    y=mdfil["sma5"], 
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < SMA25 >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="sma25",
                                    y=mdfil["sma25"], 
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < SMA75 -> PREDICT >
        if predict_flg:
            fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="predict",
                                    y=mdfil["predict"], 
                                    marker_color= 'white',
                                    mode="markers"),
                                    #line={'dash':'dot'},
                                    #mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        
        # < upper band >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="upper",
                                    y=mdfil["sma25"] + mdfil['std']*2, 
                                    #line_color= 'gray',
                                    line_color= 'gray',                                  
                                    #line={'dash':'dot'},
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < lower band >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="lower",
                                    y=mdfil["sma25"] - mdfil['std']*2, 
                                    line_color= 'gray',
                                    #line={'dash':'dot'},
                                    fill='tonexty',
                                    opacity=1,
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )

        # < sig+1 band >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="sig+1",
                                    y=mdfil["sma25"] + mdfil['std']*1, 
                                    line_color= 'yellow',
                                    line={'dash':'dot'},
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < sig-1 band >
        fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="sig-1",
                                    y=mdfil["sma25"] - mdfil['std']*1, 
                                    line_color= 'yellow',
                                    line={'dash':'dot'},
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < target rate >
        if target_rate.get(sym) != None:
            i = 1
            for rate in target_rate[sym]:
                if rate[:1].isdigit() == True:
                    #print(rate)
                    if rate.find(':') != -1:
                        col_target = rate[rate.find(':')+1:]
                        rate = rate[:rate.find(':')]
                        lcolor = 'cyan'
                    else:    
                        col_target = f"target{i}"
                        lcolor = 'blue'
                        i += 1
                    mdfil[col_target] = rate
                    fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name=col_target,
                                    y=mdfil[col_target], 
                                    #line_color= 'purple',
                                    line_color= lcolor,
                                    line=dict(width = 1),
                                    mode="lines"),
                            row = irow, 
                            col = icol   
                        )
        # < Auto-trade Buy-rate > 
        if auto_flg and buy_count > 0:
            fig = fig.add_trace( go.Scatter(x=mdf_buy.index, 
                                    name="B",
                                    y=mdf_buy, 
                                    marker_color= 'yellow',
                                    mode="markers"),
                            row = irow, 
                            col = icol   
                        )
        # < Auto-trade Sell-rate > 
        if auto_flg and sell_count > 0:
            fig = fig.add_trace( go.Scatter(x=mdf_sell.index, 
                                    name="S",
                                    y=mdf_sell, 
                                    marker_color= 'cyan',
                                    mode="markers"),
                            row = irow, 
                            col = icol   
                        )
        # < MACD >
        if macd_flg == True:
            #macd
            fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="MACD",
                                    y=mdfil["macd"], 
                                    line_color= 'green',
                                    mode="lines"),
                            row = 2, 
                            col = 1   
                        )
            #signal
            fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="signal",
                                    y=mdfil["signal"], 
                                    line_color= 'red',
                                    mode="lines"),
                            row = 2, 
                            col = 1   
                        )
            #histogram
            fig = fig.add_trace( go.Bar(x=mdfil.index, 
                                    name="histogram",
                                    y=mdfil["macd"]-mdfil["signal"],
                                    marker_color='gray'),
                            row = 2, 
                            col = 1   
                        )
            #volatility
            fig = fig.add_trace( go.Bar(x=mdfil.index, 
                                name="volatility",
                                y=mdfil["volat"], 
                                marker_color= 'yellow'),
                        secondary_y=True,
                        row = 2, 
                        col = 1   
                    )
            
            '''
            fig = fig.add_trace( go.Scatter(x=mdfil.index, 
                                    name="sma",
                                    y=mdfil["volsma"], 
                                    line_color= 'cyan',
                                    mode="lines"),
                            row = 2, 
                            col = 1   
                        )
            
            #ptc_change
            for col_name, itemSer in mdfil.items():
                #print(f"{col_name}, {idx_change}")
                if col_name == idx_change:
                    mdfil["pct_change"] = itemSer
                    mdfil["pct_change"] = mdfil["pct_change"].pct_change(prd_change).fillna(method = 'bfill')
            #
            if 'pct_change' in mdfil.columns:
                fig = fig.add_trace( go.Bar(x=mdfil.index, 
                                    name="anyone",
                                    y=mdfil["pct_change"], 
                                    marker_color= 'yellow'),
                            secondary_y=True,
                            row = 2, 
                            col = 1   
                        )
            else:
                print(f"{idx_change} is not found in columns")
            '''
        #
        # < Permutation Importance >
        if predict_flg == True and macd_flg == False:
            #importance
            fig = fig.add_trace( go.Bar(x=rslt.importances_mean, 
                                    name="mean",
                                    y=mlearn.column_names,
                                    marker_color='gray'),
                            row = 2, 
                            col = 1
                        )
            '''
            fig = fig.add_trace( go.Bar(x=rslt.importances_mean - 2 * rslt.importances_std, 
                                    name="",
                                    y=mlearn.column_names,
                                    marker_color= 'gray'),
                            row = 2, 
                            col = 1   
                        )
            fig = fig.add_trace( go.Bar(x=2 * rslt.importances_std, 
                                    name="std",
                                    y=mlearn.column_names,
                                    marker_color= 'black'),
                            row = 2, 
                            col = 1   
                        )
            '''
        #next symbol
        icount += 1
#
#
fig.update_layout(
    #autosize = False,
    title = {
        "text": "CoineCheck - Candle-Chart",
        "y": 0.9,
        "x": 0.5,
    },
    legend = legend_dict,
 )
fig.update_traces(dict(showlegend = False), selector = dict(type='candlestick'))

if selsyms[0] == '*':
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.update(layout_xaxis2_rangeslider_visible=False)
    fig.update(layout_xaxis3_rangeslider_visible=False)
    fig.update(layout_xaxis4_rangeslider_visible=False)

    fig.update_layout(
        showlegend = False
    )
else:
    if selnum == 2:
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_xaxis2_rangeslider_visible=False)
        fig.update(layout_xaxis2_showticklabels = False)
        fig.update_traces(dict(showlegend = False), row=2, col=1)
        #fig.update_xaxes(showticklabels = False)
    if macd_flg == True or predict_flg == True:
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update(layout_xaxis_showticklabels = True)
        fig.update(layout_xaxis2_showticklabels = False)
        if macd_flg == True:
            fig.update_layout(
                #xaxis_rangeslider = dict(visible=True),
                xaxis1_title = "Hour", 
                yaxis = dict(title='Rate'), 
                yaxis2= dict(title='EMA', side='left'), 
                showlegend = True
            )
            #titleStr = idx_change.upper() + "-change(%)"
            titleStr = 'Volatility(%)'
            fig.update_yaxes(title_text=titleStr, showgrid=False, 
                             range=(0.0, 0.05), secondary_y=True, 
                             row=2, col=1)
            fig.update_traces(dict(showlegend = False), row=2, col=1)
        elif predict_flg == True:
            fig.update_layout(
                #xaxis_rangeslider = dict(visible=True),
                xaxis1_title = "Hour",xaxis2_title = "Importance",
                barmode='stack',
                showlegend = True
            )
            fig.update_traces(
                dict(showlegend = False, texttemplate='%{x:0.3f}',
                    textposition='outside', orientation='h'), 
                    row=2, col=1)
            fig.update_xaxes(showticklabels = True, row=2, col=1)
#
# open the figure in  web-browser
fig.write_html('candle_figure.html', auto_open=True)
'''
fig.write_html('candle_figure.html', auto_open=False)
#
#

from selenium import webdriver
import time

# Chromeのオプション
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Selenium Serverに接続
driver = webdriver.Remote(command_executor='http://chrome:4444/wd/hub',
options=options)


try:
  # 要素の待機時間を最大3秒に設定
  driver.implicitly_wait(3)

  # candle_figure.html を開く
  file_path ='/home/seluser/mytrade/src/candle_figure.html'
  print(file_path) 
  driver.get(f"file://{file_path}")

except:
  import traceback
  traceback.print_exc()

finally:
  # Chromeを終了
  input("何かキーを押すと終了します...")
  driver.quit()
'''
#eof
