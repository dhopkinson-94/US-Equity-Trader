import TradingTracker
import TradeAutomation as ta
import pandas as pd
from datetime import  datetime
from NotificationsTele import send_notification
from Symbols import logFilePath,symbols
import os
import json
import csv

#Inital functions used to tidy up working directory
def check_last_run(filePath):
    if os.path.exists(filePath):
       ti_m = os.path.getmtime(filePath)
       now = datetime.now().timestamp()
       if now - ti_m > 3600:
          return True
       else:
          return False
    else:
       return True

def process_status(name):
    process_name = name  # change this to the name of your process
    tmp = os.popen("ps -Af").read()
    if process_name not in tmp[:]:
       return False
    else:
        return True

def check_directory(path):
    if os.path.exists(path):
       return
    else:
       os.makedirs(path, mode=0o777, exist_ok=False)
       return

def clean_logfile(filePath):
    logFile = open(filePath,'r')
    lines = logFile.readlines()
    length = len(lines) - 500
    lines = lines[length:]
    logFile.close()
    with open(filePath,'w') as f:
        f.writelines(lines)
    f.close()

def order_file(path):
    myColumns = ['Timestamp','Symbol','ID','Quantity','Price','Side','Limit Price','ROI']
    df = pd.DataFrame(columns=myColumns)
    df.to_csv(path+'Orders.csv')




if __name__ == "__main__":
   clean_logfile(logFilePath)
   file = open(logFilePath,'a')
   returns = {}
   order1 = ta.TakeOrder()
   cash = float(json.loads(order1.account_request().json())['cash'])
   for pair in symbols:
       datadir = f'{pair[0]}-{pair[1]}/'
       check_directory(datadir)
       if not os.path.isfile(datadir+'Orders.csv'):
           order_file(datadir)
       data = order1.req_historical_data(pair)
       data[pair[0]].to_csv(datadir + f'{pair[0]}.csv')
       data[pair[1]].to_csv(datadir + f'{pair[1]}.csv')
       values = TradingTracker.make_pairs_csv(pair)
       signals = values[0]
       returns[pair] = max(values[1])
       send_notification(f'{datetime.now()} - Signals: {signals}, Pair: {pair}.')
       if sum(signals) > 0:
           trade = ta.format_request(signals)
           result = f"{datetime.now()} - Error - Method: format_request - No key found."
           file.write(f'\n{datetime.now()} - Signal detected {signals}.')
           order = ta.TakeOrder(pair,cash)
           if trade: result = order.check_position(trade)
           send_notification(result)
           file.write(result)
       else:
           file.write(f'\n{datetime.now()} - (TakeOrder) - No signal today.')
           send_notification(f'{datetime.now()} - (TakeOrder) - No signal found.')
   print(returns)
   file.write(f'\n{datetime.now()} - Max returns: {returns}.')
   account = order1.account_request()
   pnl = order1.get_portfolio_PL()
   position = order1.get_all_positions(), order1.get_all_orders(), account
   send_notification(f'{datetime.now()} - Positions: {position[0]} \n\n\nOpen Orders: {position[1]}'
                     f'\n\n\nBuying Power: {position[2]}\n\n\n'
                     f'{pnl}')





