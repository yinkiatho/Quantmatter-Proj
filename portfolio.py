from __future__ import division
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit
from keras.models import Sequential
from keras.layers import Dense, Dropout, BatchNormalization, Conv1D, Flatten, MaxPooling1D, LSTM
from keras.callbacks import EarlyStopping, ModelCheckpoint, TensorBoard
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import pandas_ta as ta
import seaborn as sns
import metrics as metrics
from collections import OrderedDict, defaultdict

#import from other files
from position import Position

"""
ticker_list = [
    'AAPL',
    'MSFT',
    'AMZN',
    'GOOGL',
    'NVDA',
    'TSLA',
    'META',
    'GOOG',
    'XOM',
    'UNH',
    'JPM',
    'LLY',
    'JNJ',
    'V',
    'PG',
    'AVGO',
    'MA',
    'HD',
    'CVX',
    'ABBV',
    'MRK',
    'COST',
    'PEP',
    'WMT',
    'ADBE',
    'CSCO',
    'KO',
    'CRM',
    'TMO',
    'ACN'
]

"""

#['WDC', 'UNP', 'MOS', 'SPG', 'WAB', 'TRGP', 'URI', 'TPR', 'WYNN',
#               'BA', 'CI', 'DIS', 'TDG', 'VRTX', 'TMO', 'ULTA', 'HD', 'WHR', 'GWW', 'GS']

ticker_list =  ['SO',
 'ZTS',
 'WMT',
 'SYF',
 'PG',
 'CLX',
 'HSY',
 'XEL',
 'WEC',
 'VZ',
 'KO',
 'SYY',
 'TGT',
 'SJM',
 'KR',
 'SRE',
 'WBA',
 'XYL',
 'WELL',
 'WM',
 'UPS',
 'TJX',
 'TSN',
 'VTR',
 'TRV',
 'SNPS',
 'SHW',
 'HD',
 'YUM',
 'PGR',
 'UNH',
 'SPG',
 'ZBH',
 'SYK',
 'VRSN',
 'VFC',
 'ALL',
 'NOW',
 'V',
 'SBUX',
 'GWW',
 'EL',
 'TRGP',
 'CI',
 'BA',
 'TDG',
 'ULTA',
 'DIS',
 'WBD',
 'TSCO']

class PortfolioTrader():

    def __init__(self, quantity=50, cash=1000000, max_active_positions= 10, percent_slippage = 0.0005, trade_fee=1, stop_loss=0.15, target=0.05):
        
        
        print("Initializing PortfolioTrader...")
        self.models_dict = {ticker: pd.read_csv("ML Models/stock_selection/data/" + ticker + ".csv",
                           index_col="Date", parse_dates=True) for ticker in ticker_list}
        self.logged_positions = {ticker: []
                                 for ticker in ticker_list}  # : Ticker: List[Position]
        
        self.quantity = quantity
        self.stop_loss = stop_loss
                
        #Cash series
        self.cash = cash
        self.cash_history = {} #date: cash
        self.PnL = {} #date: PnL
        
        #Stock allocation of portfolio
        self.stock_allocation = {ticker: 0 for ticker in ticker_list} #ticker: total value of shares
        self.current_positions = 0
        
        #Trade parameters
        self.max_active_positions = max_active_positions
        self.percent_slippage = percent_slippage
        self.trade_fee = trade_fee
        self.target = target
        self.simulation_finished = False
        
        #Dates
        self.current_date = "2015-01-01"
        self.last_date = "2015-01-01"
        self.start_date = "2015-01-01"
        self.end_date = "2020-12-31"
        
        #Result Summaries data frame
        self.metrics = pd.DataFrame(columns=['Stop Loss', 'Quantity Shares Traded', 'Max Active Positions', 'Target', 
                                           'Sharpe Ratio', 'Max Drawdown', 'Annualized return', 'PnL'])
        
        self.hit_rate = {
            'success': 0,
            'fail': 0
        }


    def add_to_history(self, position: Position):
        _log = self.logged_positions
        assert not position in _log, 'Recorded the same position twice.'
        assert position.is_closed, 'Position is not closed.'
        self.logged_positions.add(position)
        self.position_history.append(position)
        self.last_date = max(self.last_date, position.last_date)


    def record_cash(self, date, cash):
        self.cash_history[datetime.datetime.strptime(date, '%Y-%m-%d')] = cash
        self.last_date = max(self.last_date, date)
        
        
    def record_PNL(self, date, pnl):
        self.PnL[datetime.datetime.strptime(date, '%Y-%m-%d')] = pnl
        self.last_date = max(self.last_date, date)

    
                
                
    def check_to_open_long_positions(self, ticker, price):
        
        if self.cash < self.quantity * price or self.current_positions >= self.max_active_positions or self.cash <= 0:
            #print("Not enough cash and can't open long position")
            return False
        else:
            return True
        

    def check_to_open_short_positions(self, ticker, price):
        
        if self.cash < self.quantity * price or self.current_positions >= self.max_active_positions:
            #print("Not enough cash and can't open short position")
            return False  
        else:
            #Open position
            return True
    
                
            
    def simulate_day(self, date):
        
        current_cash = self.cash
        day_PnL = 0

        for ticker in ticker_list:
            #Access row by date index
            try:
                current_data = self.models_dict[ticker].loc[self.current_date]
            except KeyError:
                #print(f"No data for {ticker} on {date}")
                continue
                        
            signal = current_data["position"]
            current_price = current_data["Close"]
            
            # Update current price in position histories and logged positions
            new_posistions = []
            for position in self.logged_positions[ticker]:
                #print(f"Updating {ticker} position")
                if position.is_active:
                    position.record_price_update(self.current_date, current_price)
                
                if position.is_active and (position.stop_loss_hit() or position.target_hit()) and position.type == "long": 
                #or (position.is_active and position.type == "long") and signal == -1:
                    position.exit(self.current_date, current_price)
                    self.current_positions -= 1

                    # Update stock allocation
                    self.stock_allocation[ticker] -= position.last_price * \
                        position.shares
            
                    # Update cash
                    current_cash += position.last_price * position.shares - self.trade_fee                    
                    day_PnL += position.return_value
                    
                    #Update Hit Rate
                    if position.is_successful:
                        self.hit_rate['success'] += 1
                    else:
                        self.hit_rate['fail'] += 1

                elif position.is_active and (position.stop_loss_hit() or position.target_hit()) and position.type == "short": 
                #or (position.is_active and position.type == "short" and signal == 1):
                    
                    if self.cash > self.quantity * current_price:
                        position.exit(self.current_date, current_price)
                        self.current_positions -= 1

                        # Update stock allocation
                        self.stock_allocation[ticker] -= position.last_price * \
                            position.shares

                        # Update cash
                        current_cash -= (position.last_price * position.shares + self.trade_fee)
                        day_PnL += position.return_value
                    
                        # Update Hit Rate
                        if position.is_successful:
                            self.hit_rate['success'] += 1
                        else:
                            self.hit_rate['fail'] += 1
                
                if position.is_active:
                    new_posistions.append(position)
            
            
            #Update positions after closing
            self.logged_positions[ticker] = new_posistions
            
            if signal == 1:
                #print("Long signal for " + ticker)
                canOpen = self.check_to_open_long_positions(
                    ticker, current_price)
                
                if canOpen:
                    
                    current_stock_allocation = self.stock_allocation[ticker]
                    #Open new Position and update position logs
                    position = Position(
                        ticker, self.current_date, "long", current_price, self.quantity, self.stop_loss, self.target)
                    
                    assert not position.is_closed, 'Position is not closed.'
                    self.logged_positions[ticker].append(position)
                    self.current_positions += 1
                    
                    #Update Cash and stock allocation
                    current_cash -= self.quantity * current_price * \
                        (1 + self.percent_slippage) + self.trade_fee
                    current_stock_allocation += self.quantity * \
                        current_price * (1 + self.percent_slippage)
                        
                    self.stock_allocation[ticker] = current_stock_allocation
            
            elif signal == -1:
                canShort = self.check_to_open_short_positions(
                    ticker, current_price)
                
                if canShort:
                    
                    current_stock_allocation = self.stock_allocation[ticker]
                    #Open new Position and update position logs
                    position = Position(
                        ticker, self.current_date, "short", current_price, self.quantity, self.stop_loss, self.target)
                    
                    self.logged_positions[ticker].append(position)
                    self.current_positions += 1
                    
                    #Update Cash and stock allocation
                    current_cash += self.quantity * current_price * \
                        (1 - self.percent_slippage) - self.trade_fee
                    current_stock_allocation += self.quantity * \
                        current_price * (1 - self.percent_slippage)
                    self.stock_allocation[ticker] = current_stock_allocation
        
        #Update daily PnL
        self.cash = current_cash   
        self.record_PNL(self.current_date, day_PnL)
        
        #print(f"Current date: {self.current_date} + PnL: {day_PnL}")
        #print(f"EOD Positions: {self.current_positions}")
                    
    def simulate(self):
        
        while not self.simulation_finished and datetime.datetime.strptime(self.current_date, '%Y-%m-%d') < datetime.datetime.strptime(self.end_date, '%Y-%m-%d'):

            self.simulate_day(self.current_date)
            #print(f"Current date: {self.current_date} + Cash: {self.cash}")
            self.record_cash(self.current_date, self.cash)
            self.current_date = (datetime.datetime.strptime(
                self.current_date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            
        self.close_profit_positions()
        print("Simulation finished")
        
    def close_all_positions(self):
        
        for ticker in ticker_list:
            for position in self.logged_positions[ticker]:
                if position.is_active and position.type == "long":
                    position.exit(self.current_date, position.last_price)
                    
                    # Update stock allocation
                    self.stock_allocation[ticker] -= position.last_price * \
                        position.shares

                    # Update cash
                    self.cash += position.last_price * position.shares - self.trade_fee
                    #print(f"New cash: {self.cash}")
                    
                elif position.is_active and position.type == "short":
                    position.exit(self.current_date, position.last_price)
                    
                    # Update stock allocation
                    self.stock_allocation[ticker] -= position.last_price * \
                        position.shares

                    # Update cash
                    self.cash -= position.last_price * position.shares - self.trade_fee
                    #print(f"New cash: {self.cash}")
                    
    def close_profit_positions(self):

        for ticker in ticker_list:
            for position in self.logged_positions[ticker]:
                if position.is_active and position.type == "long" and position.last_price > position.entry_price:
                    position.exit(self.current_date, position.last_price)

                    # Update stock allocation
                    self.stock_allocation[ticker] -= position.last_price * \
                        position.shares

                    # Update cash
                    self.cash += position.last_price * position.shares - self.trade_fee
                    #print(f"New cash: {self.cash}")

                elif position.is_active and position.type == "short" and position.last_price < position.entry_price:
                    position.exit(self.current_date, position.last_price)

                    # Update stock allocation
                    self.stock_allocation[ticker] -= position.last_price * \
                        position.shares

                    # Update cash
                    self.cash -= position.last_price * position.shares - self.trade_fee

    def plot_cash(self):
        cash_history = pd.Series(self.cash_history)
        cash_history.plot(figsize=(20, 10))
        plt.title('Cash over time', fontsize=20)
        plt.xlabel('Date', fontsize=20)
        plt.ylabel('Cash', fontsize=20)
        plt.grid(axis='both')
        plt.show()
        
    
    def calculate_metrics(self):
        cash_history = pd.Series(self.cash_history)
        pnl_history = pd.Series(self.PnL)
        
        #Calculate total PnL
        total_PnL = pnl_history.sum()
        cumsum_PnL = pnl_history.cumsum()
        self.cumsumPnL = cumsum_PnL

        # Calculate annualized return
        annualized_return = metrics.calculate_cagr(cash_history)

        # Calculate Sharpe Ratio
        sharpe = metrics.calculate_sharpe_ratio(cash_history)

        # Calculate Max Drawdown
        max_drawdown = metrics.calculate_max_drawdown(cash_history)

        # Add to metrics data frame

        # ['Stop Loss', 'Quantity Shares Traded', 'Max Active Positions',
        #                                   'Sharpe Ratio', 'Max Drawdown', 'Annualized return']
        self.metrics = pd.concat([self.metrics, pd.DataFrame({'Stop Loss': [self.stop_loss], 
                                                              'Quantity Shares Traded': [self.quantity], 
                                                              'Max Active Positions': [self.max_active_positions / 50],
                                                              'Target': [self.target],
                                                              'Sharpe Ratio': [sharpe], 
                                                              'Max Drawdown': [max_drawdown], 
                                                              'Annualized return': [annualized_return],
                                                              'PnL': [total_PnL]
                                                              })], 
                                 axis=0, ignore_index=True)
        
    def print_summary(self):
        
        # Calculate annualized return
        print(f"Annualized return: {self.metrics['Annualized return'].iloc[0]}")
        
        # Calculate Sharpe Ratio
        print(f"Sharpe Ratio: {self.metrics['Sharpe Ratio'].iloc[0]}")
        
        # Calculate Max Drawdown
        print(f"Max Drawdown: {self.metrics['Max Drawdown'].iloc[0]}")
        
        # Calculate Sortino Ratio
                
        # Hit Rate
        print(f"Hit Rate: {self.hit_rate['success'] / (self.hit_rate['success'] + self.hit_rate['fail'])}")
        
        # P & L
        print(f"P & L: {self.metrics['PnL'].iloc[0]}")


    def plot_profit(self):
        
        self.cumsumPnL.plot(figsize=(20, 10))
        plt.title('Cumulative P&L over time', fontsize=20)
        plt.xlabel('Date', fontsize=20)
        plt.ylabel('Profit', fontsize=20)
        plt.grid(axis='both')
        plt.show()
        
        
