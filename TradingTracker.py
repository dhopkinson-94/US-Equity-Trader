import PairStrategyScript
from datetime import  datetime
from Symbols import logFilePath

def make_pairs_csv(pair):
  file = open(logFilePath, 'a')
  file.write(f'\n{datetime.now()} - Trading Tracker initiated.')
  datadir = f'{pair[0]}-{pair[1]}/'
  ps = PairStrategyScript.PairsStrategy(pair)
  file.write(f'\n{datetime.now()} - pairs trading class initiated.')
  lookbacks = range(50,210,10)
  returns = []

  #Initiates loop through lookback ranges
  biggest_return = 0
  for lb in lookbacks:
      pairs = ps.create_pairs_dataframe(datadir,pair)
      pairs = ps.calc_spread_zscore(pairs, pair, lookback=lb)
      pairs = ps.create_long_short_market_signals(
      pairs, pair, z_entry_threshold=1.5, z_exit_threshold=0.5
      )
      portfolio = ps.create_portfolio_returns(pairs, pair, 5000)
      returns.append(float(portfolio[1]))
      for i in range(len(returns)):
          if returns[i] > biggest_return:
              biggest_return = returns[-1]
              portfolio[0].to_csv( datadir + f'{pair[0]}-{pair[1]}_portfolio_return.csv')
              file.write(f'\n{datetime.now()} - portfolio returns csv updated.')
              pairs.to_csv(datadir + f'{pair[0]}-{pair[1]}_pairs.csv')
              file.write(f'\n{datetime.now()} - pairs csv updated.')
              first = pairs.iat[len(pairs) - 1, 8]
              second = pairs.iat[len(pairs) - 1, 9]
              third = pairs.iat[len(pairs) - 1, 10]
              fourth = pairs.iat[len(pairs) - 1, 11]
              fifth = pairs.iat[len(pairs) - 1, 12]
              sixth = pairs.iat[len(pairs) - 2, 11]
              seventh = pairs.iat[len(pairs) - 2, 12]
              signals = (first,second,third,fourth,fifth,sixth,seventh)

  file.write(str(signals))
  file.close()
  return signals,returns

  #breakpoint()
  #file.close()



  #print("Plotting the performance charts...")
 # fig = plt.figure()

  #ax1 = fig.add_subplot(211, ylabel='%s growth (%%)' % symbol[0])
  #(pairs['%s_close' % symbol[0].lower()].pct_change() + 1.0).cumprod().plot(ax=ax1, color='r', lw=2.)

  #ax2 = fig.add_subplot(212, ylabel='Portfolio value growth (%%)')
  #returns.plot(ax=ax2, lw=2.)

  #plt.show()


# adds signals to list and passes them to trade automation script.









