# Portfolio RSI Inter-Day Trading Strategy
================

## RSI Strategy:

### Constraints:
- Maximum positions opened per day for each stock = 1

### Stock Selection and Pre-processing
- Out of the top 100 stocks in market cap in S&P500 universe, select the 50 stocks that will have the least covariance with other stocks, leading to overall least portfolio covariance
- Add RSI signal based on Close price, shift signal to avoid look-ahead bias


### Initialization State:
- Cash: 1000000
- Stocks Universe: Top 30 SP500 Stocks in Market Capitalization

### Trading Strategy for each stock:

- If Stop-Loss hit or target hit or RSI(7) < 30:
    - Close all short positions
    - Execute a buy order at current price and specified volume

- If Stop-Loss hit or target hit or RSI(7) > 70:
    - Close all long positions
    - Execute a short order at current price and specified volume


### Optimal Portfolio Parameters:

## Optimization Procedure
- Grid search with parameters:
(1) Max active positions per stock
(2) Stop Loss
(3) Profit Target
(4) Quantity of shares traded per order

- Aim to obtain parameters with positive P&L, best Sharpe Ratio and > 0.6 hit rate.


## Optimized Parameters
- Stop-Loss: None
- Profit-Taking Level: None
- Amount of shares per order: 20
- Maximum number of opened positions allowed: 30 * 10


### Result Statistics:
- Net Profit: $452157
- Annualized Return: 5.02%
- Sharpe Ratio: 0.0794
- Max Drawdown: 0.804
- Hit Rate: 0.642



