import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict, defaultdict


class Position(object):

    def __init__(self, ticker, entry_date, type,
                 entry_price, shares, stop_loss, target=0.05):

        # Recorded on initialization
        self.entry_date = entry_date

        assert entry_price > 0, 'Cannot buy asset with zero or negative price.'
        self.entry_price = entry_price
        
        self.type = type

        assert shares > 0, 'Cannot buy zero or negative shares.'
        self.shares = shares

        self.ticker = ticker
        
        if type == "long":
            self.stop_loss = entry_price * (1 - stop_loss)
        else:
            self.stop_loss = entry_price * (1 + stop_loss)
            
        if type == "long":
            self.target = entry_price * (1 + target)
        else:
            self.target = entry_price * (1 - target)
            
        # Recorded on position exit
        self.exit_date = None
        self.exit_price = None

        # For easily getting current portfolio value
        self.last_date = None
        self.last_price = None

        # Updated intermediately
        self._dict_series = OrderedDict()
        self.record_price_update(entry_date, entry_price)

        # Cache control for pd.Series representation
        self._price_series: pd.Series = None
        self._needs_update_pd_series: bool = True

    def exit(self, exit_date, exit_price):
        
        assert self.entry_date != exit_date, 'Churned a position same-day.'
        assert not self.exit_date, 'Position already closed.'
        self.record_price_update(exit_date, exit_price)
        self.exit_date = exit_date
        self.exit_price = exit_price
        #print(f'Exited {self.ticker} position on {exit_date} at ${exit_price:.2f}')

    def record_price_update(self, date, price):
        
        self.last_date = date
        self.last_price = price
        self._dict_series[date] = price
        #print(f'Updated {self.ticker} position on {date} at ${price:.2f}')

        # Invalidate cache on self.price_series
        self._needs_update_pd_series = True
        
    def stop_loss_hit(self):
        if self.type == "long":
            if self.last_price <= self.stop_loss:
                return True
        else:
            if self.last_price >= self.stop_loss:
                return True
        return False
    
    def target_hit(self):
        if self.type == "long":
            if self.last_price >= self.target:
                return True
        else:
            if self.last_price <= self.target:
                return True
        return False

    @property
    def price_series(self):
       
        if self._needs_update_pd_series or self._price_series is None:
            self._price_series = pd.Series(self._dict_series)
            self._needs_update_pd_series = False
        return self._price_series

    @property
    def last_value(self):
        return self.last_price * self.shares

    @property
    def is_active(self):
        return self.exit_date is None
    
    @property
    def is_successful(self):
        assert not self.is_active, 'Position must be closed to access this property'
        if self.type == "long":
            return self.exit_price >= self.entry_price
        else:
            return self.exit_price <= self.entry_price

    @property
    def is_closed(self):
        return not self.is_active

    @property
    def value_series(self):
        """
        Returns the value of the position over time. Ignores self.exit_date.
        Used in calculating the equity curve.
        """
        assert not self.is_active, 'Position must be closed to access this property'
        return self.shares * self.price_series[:-1]

    @property
    def percent_return(self):
        return (self.exit_price / self.entry_price) - 1

    @property
    def entry_value(self):
        return self.shares * self.entry_price
    
    @property
    def return_value(self):
        if self.type == "long":
            return self.shares * (self.exit_price - self.entry_price)
        else:
            return self.shares * (self.entry_price - self.exit_price)
        

    @property
    def exit_value(self):
        return self.shares * self.exit_price

    @property
    def change_in_value(self):
        return self.exit_value - self.entry_value

    @property
    def trade_length(self):
        return len(self._dict_series) - 1

    def print_position_summary(self):
        _entry_date = self.entry_date
        _exit_date = self.exit_date
        _days = self.trade_length

        _entry_price = round(self.entry_price, 2)
        _exit_price = round(self.exit_price, 2)

        _entry_value = round(self.entry_value, 2)
        _exit_value = round(self.exit_value, 2)

        _return = round(100 * self.percent_return, 1)
        _diff = round(self.change_in_value, 2)

        print(f'{self.ticker:<5}     Trade summary')
        print(f'Date:     {_entry_date} -> {_exit_date} [{_days} days]')
        print(f'Price:    ${_entry_price} -> ${_exit_price} [{_return}%]')
        print(f'Value:    ${_entry_value} -> ${_exit_value} [${_diff}]')
        print()

    def __hash__(self):
        """
        A unique position will be defined by a unique combination of an 
        entry_date and ticker, in accordance with our constraints regarding 
        duplicate, variable, and compound positions
        """
        return hash((self.entry_date, self.ticker))
