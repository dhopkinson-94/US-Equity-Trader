
"""" ---------Strategy Script----------

Place your trading strategy in this script. Ideally imports timeseries price dataframes from the tickers folder, analyses the data, 
backtests the strategy saving the data to a csv file.

args:
  sym/syms (String or list of Strings)  Tickers to identify trading signal
   
initial variables:
  sym/syms
   
returns:
  None

"""""


Class Strategy:
    def __init__(self, pairs):
        self.pairs = pairs

    def create_pairs_dataframe(self, datadir):
        return

    def create_long_short_market_signals(self):
        return
     
