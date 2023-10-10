import numpy as np
import pandas as pd

def calculate_return_series(series):
    shifted_series = series.shift(1, axis=0)
    return series / shifted_series - 1


def calculate_log_return_series(series):
    shifted_series = series.shift(1, axis=0)
    return pd.Series(np.log(series / shifted_series))


def calculate_percent_return(series):
    #Percent return of last value / first value
    return series.iloc[-1] / series.iloc[0] - 1


def get_years_past(series):
    start_date = series.index[0]
    end_date = series.index[-1]
    return (end_date - start_date).days / 365.25


def calculate_cagr(series):
    
    #Calculate compounded annual growth rate
    start_price = series.iloc[0]
    end_price = series.iloc[-1]
    value_factor = end_price / start_price
    year_past = get_years_past(series)
    return (value_factor ** (1 / year_past)) - 1


def calculate_annualized_volatility(return_series):
    #Calculates annualized volatility for a date-indexed return series. 
    #Works for any interval of date-indexed prices and returns.
    years_past = get_years_past(return_series)
    entries_per_year = return_series.shape[0] / years_past
    return return_series.std() * np.sqrt(entries_per_year)


def calculate_sharpe_ratio(price_series,
                           benchmark_rate: float = 0):
    #Calculates the Sharpe ratio given a price series. Defaults to benchmark_rate
    #of zero.
    cagr = calculate_cagr(price_series)
    return_series = calculate_return_series(price_series)
    volatility = calculate_annualized_volatility(return_series)
    return (cagr - benchmark_rate) / volatility


def calculate_rolling_sharpe_ratio(price_series,
                                   n: float = 20):
    #Compute an approximation of the Sharpe ratio on a rolling basis. 
    #Intended for use as a preference value.
    rolling_return_series = calculate_return_series(price_series).rolling(n)
    return rolling_return_series.mean() / rolling_return_series.std()


def calculate_annualized_downside_deviation(return_series,
                                            benchmark_rate: float = 0):
    #Calculates the downside deviation for use in the Sortino ratio.

    #Benchmark rate is assumed to be annualized. It will be adjusted according
    #to the number of periods per year seen in the data.
    
    # For both de-annualizing the benchmark rate and annualizing result
    years_past = get_years_past(return_series)
    entries_per_year = return_series.shape[0] / years_past

    adjusted_benchmark_rate = ((1+benchmark_rate) ** (1/entries_per_year)) - 1

    downside_series = adjusted_benchmark_rate - return_series
    downside_sum_of_squares = (downside_series[downside_series > 0] ** 2).sum()
    denominator = return_series.shape[0] - 1
    downside_deviation = np.sqrt(downside_sum_of_squares / denominator)

    return downside_deviation * np.sqrt(entries_per_year)


def calculate_sortino_ratio(price_series,
                            benchmark_rate: float = 0):
    #Calculates the Sortino ratio.
    cagr = calculate_cagr(price_series)
    return_series = calculate_return_series(price_series)
    downside_deviation = calculate_annualized_downside_deviation(return_series)
    return (cagr - benchmark_rate) / downside_deviation


DRAWDOWN_EVALUATORS = {
    'dollar': lambda price, peak: peak - price,
    'percent': lambda price, peak: -((price / peak) - 1),
    'log': lambda price, peak: np.log(peak) - np.log(price),
}


def calculate_drawdown_series(series, method: str = 'percent'):
    #Returns the drawdown series
    evaluator = DRAWDOWN_EVALUATORS[method]
    return evaluator(series, series.cummax())


def calculate_max_drawdown(series, method: str = 'percent'):
    #Simply returns the max drawdown as a float
    return calculate_drawdown_series(series, method).max()



def calculate_log_max_drawdown_ratio(series):
    log_drawdown = calculate_max_drawdown(series, method='log')
    log_return = np.log(series.iloc[-1]) - np.log(series.iloc[0])
    return log_return - log_drawdown


def calculate_calmar_ratio(series, years_past: int = 3):

    #Return the percent max drawdown ratio over the past three years

    # Filter series on past three years
    last_date = series.index[-1]
    three_years_ago = last_date - pd.Timedelta(days=years_past*365.25)
    series = series[series.index > three_years_ago]

    # Compute annualized percent max drawdown ratio
    percent_drawdown = calculate_max_drawdown(series, method='percent')
    cagr = calculate_cagr(series)
    return cagr / percent_drawdown
