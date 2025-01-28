from Symbols import logFilePath,symbols
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.requests import StockLatestQuoteRequest
from datetime import datetime,timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest,MarketOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest,GetAssetsRequest,StopOrderRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus,TimeInForce,OrderClass
import secrets
import string
import json
import pandas as pd
import sys
import os



"""" 
Function takes most recent signal data and identifies if there is a buy or sell opportunity.

 args:
   signals (list/tuple) - can be any buy or sell signal used in your trading strategy

 returns:
   sig (str or none) - returns the appropriate signal
 
"""""
def format_request(signals):
    func_dict = {(1.0,0.0,0.0,1.0,0.0,0.0,0.0):'BUY',
                 (0.0,1.0,0.0,0.0,1.0,0.0,0.0):'BUY',
                 (0.0,0.0,1.0,0.0,0.0,1.0,0.0):'SELL',
                 (0.0,0.0,1.0,0.0,0.0,0.0,1.0):'SELL',
                 (1.0,0.0,0.0,1.0,0.0,1.0,0.0):'BUY',
                 (0.0,1.0,0.0,0.0,1.0,0.0,1.0):'BUY',
                 (0.0,0.0,1.0,0.0,0.0,0.0,0.0):'SELL',
                 'req_data': None,
                 'price': None,
                 'Query':None}
    print(signals)
    try:
       sig = func_dict[signals]
    except KeyError:
        return None
    return sig


"""" ---------TAKEORDER CLASS----------

Used to send and receive information and orders to the alpaca API. Currently only sends basic
bracket buy orders and no short sells.

args:
  syms (tuple) - list of stock symbols where order is required
   
  cash (float) - Amount of cash available on alapca account before trades are placed
   
initial variables:
  paper (bool) - True if you are using a paper(not production) alpaca account, False if live trading account.
  
  prefix (char) - "p" if paper is true and "s" if not
   
  datadir (str) - Path to folder where stock data is kept
   
  logfile (file) - Open txt file to concat to
   
tokens:
  use os.environ[""] to retrieve git secrets used to access alpaca account

returns:
  None

"""""
class TakeOrder:

    def __init__(self,pair=None,cash=None):

        self.paper = True
        self.prefix = 'p'
        if os.environ["live"]=='live':
           self.paper = False
           self.prefix = 'l'
        self.pair = pair
        if self.pair:
           self.datadir = f'{pair[0]}-{self.pair[1]}/'
        if not self.paper: self.prefix = 'l'
        self.logfile = open(logFilePath, 'a')
        self.logfile.write(f'\n{datetime.now()} - (TakeOrder) instance initialised')
        self.buying_power = cash



#initial functions

    #sends request to alapca to retrieve associated account information (cash, buying power etc.)
    def account_request(self):
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'],paper=self.paper)
        account = trading_client.get_account()
        # Check if our account is restricted from trading.
        if account.trading_blocked:
            print('Account is currently restricted from trading.')
        # Check how much money we can use to open new positions.
        return account


    # Returns a dictionary of all open positions on alapca account
    def get_all_positions(self):
        positions = {}
        for pair in symbols:
            for sym in pair:
                positions[sym] = None
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'],paper=self.paper)
        trading_client.get_all_positions()
        # Get a list of all of our positions.
        portfolio = trading_client.get_all_positions()
        for position in portfolio:
            positions[position.symbol] = position.qty
        return positions


    #Requests historical price data of a list of stock symbols and returns them as panadas dataframes in a dictionary
    def req_historical_data(self,syms):
        d = datetime.now() - timedelta(days=0)
        dataDict = {}
        for sym in syms:
            client = StockHistoricalDataClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'])
            request_params = StockBarsRequest(
                symbol_or_symbols=sym,
                timeframe=TimeFrame.Day,
                start=datetime(2018, 8, 1),
                end=d.date()
            )
            bars = client.get_stock_bars(request_params)
            data = bars.df
            data.reset_index(inplace=True)
            time = data['timestamp']
            close = data['close']
            data = pd.concat([time, close], axis=1)
            dataDict[sym] = data
        return dataDict

    
    def current_price(self,sym):
        prices={}
        client = StockHistoricalDataClient(os.environ['lKey'], os.environ['lSecret'])
        # single symbol request
        request_params = StockLatestQuoteRequest(symbol_or_symbols=sym)
        latest_quote = client.get_stock_latest_quote(request_params)
        # must use symbol to access even though it is single symbol
        prices[sym]=float(latest_quote[sym].ask_price)
        return prices

    #ORDER FUNCTIONS
    # Checks last order made to ensure order is not made more than once
    def send_order(self,sym):
        capital = self.buying_power
        price = self.current_price(sym)
        multiplier = 1.1
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'], paper=self.paper)
        if price[sym] == 0:
           return f'{datetime.now()} - Last quote data returning as 0, order cancelled'
        quantity = int((capital / (len(symbols) * 2)) / price[sym])
        if 1 <= quantity < 3:
           multiplier = 1.1
        if quantity > 3:
           multiplier = 1.15
        if quantity < 1:
           return f'{datetime.now()} - Buy order quantity < 1, Order cancelled {sym, quantity}'
        order_data = MarketOrderRequest(
            symbol=sym,
            qty=quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(price[sym] * multiplier, 2)),
            stop_loss=StopLossRequest(stop_price=round(price[sym] * 0.5, 2)),
            
        )
        try:
            market_order = trading_client.submit_order(
                order_data=order_data
            )
        except:
            the_type, the_value, the_traceback = sys.exc_info()
            # Logs the error appropriately.
            return self.format_error(sym,the_type,the_value,the_traceback)

        self.log_orders(market_order)
        return self.format_order(sym,market_order)



    def exit_position(self,sym):
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'], paper=self.paper)
        orders = self.get_all_orders()
        positions = self.get_all_positions()
        for order in orders['SELL']:
            if order.symbol == sym:
                trading_client.cancel_order_by_id(order.id)
        quantity = int(positions[sym])
        order_data = MarketOrderRequest(
            symbol=sym,
            qty=quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        if quantity < 1:
            return f'{datetime.now()} - Sell attempted whilst there was no position, order cancelled {sym, quantity}'
        try:
            market_order = trading_client.submit_order(
                order_data=order_data
            )
        except:
            the_type, the_value, the_traceback = sys.exc_info()
            # Logs the error appropriately.
            return self.format_error(sym,the_type,the_value,the_traceback)

        self.log_orders(market_order)
        return self.format_order(sym,market_order)



    #Iterates through pairs and sending orders if signal is found. Returns (String) message either error or order details
    def check_position(self,action):
        positions = self.get_all_positions()
        update = 'Trading Update: '
        for sym in self.pair:
            if not action:
               update = update + f'\n{datetime.now()} - No action for {sym} required.'
            if action == 'BUY':
                if not positions[sym]:
                    data = self.send_order(sym)
                    update = update + f'\n{data}'
                else:
                    update = update + f'\n{datetime.now()} - Open position exists for {sym} - no buy today.'
            if action == 'SELL':
                if positions[sym]:
                    data = self.exit_position(sym)
                    update = update + f'\n{data}'
                else:
                    update = update + f'\n{datetime.now()} - No position exists for {sym} - no sell today.'
        return update

    def get_all_orders(self):
        bidAskOrder = {'BUY':'','SELL':''}
        for key in bidAskOrder.keys():
            if key == 'BUY':
               side = OrderSide.BUY
            else:
               side = OrderSide.SELL
            trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'], paper=self.paper)
            # params to filter orders by
            request_params = GetOrdersRequest(
                status=QueryOrderStatus.OPEN,
                side=side)
            # orders that satisfy params
            orders = trading_client.get_orders(filter=request_params)
            bidAskOrder[key] = orders
        return bidAskOrder

    def get_order(self, ID):
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'], paper=self.paper)
        my_order = trading_client.get_order_by_client_id(ID)
        return my_order.id

    def cancel_all_orders(self):
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'], paper=self.paper)
        # attempt to cancel all open orders
        cancel_statuses = trading_client.cancel_orders()
        return cancel_statuses

    def get_portfolio_PL(self):
        trading_client = TradingClient(os.environ[self.prefix+'Key'], os.environ[self.prefix+'Secret'],paper=self.paper)

        # Get our account information.
        account = trading_client.get_account()

        # Check our current balance vs. our balance at the last market close
        balance_change = float(account.equity) - float(account.last_equity)
        return f'Today\'s portfolio balance change: ${balance_change}'

    def format_error(self,sym,the_type,the_value,the_traceback):
       return f'{datetime.now()} - Market order for {sym} failed. Check code!' \
              f'\nType: {the_type}' \
              f'\nValue: {the_value}' \
              f'\nTraceback: {the_traceback}'

    def format_order(self,sym,market_order):
        return f'{datetime.now()} - Market order for {sym} executed.' \
               f'\n--------ORDER--------' \
               f'\nClass: {market_order.order_class}' \
               f'\nSymbol: {market_order.symbol}' \
               f'\nQuantity: {market_order.qty}' \
               f'\nSide: {market_order.side}' \
               f'\nLimit: {market_order.limit_price}'

    def log_orders(self,order):
        roi = 0.0
        if order.side == "Sell": roi = order.status

        orders = pd.read_csv(self.datadir+'Orders.csv',
            header=0,
            index_col=0,
        )
        orders.loc[len(orders)] = [datetime.now(),order.symbol,order.id,order.qty,order.filled_avg_price,order.side,order.limit_price,roi]
        orders.to_csv(self.datadir+'Orders.csv')

