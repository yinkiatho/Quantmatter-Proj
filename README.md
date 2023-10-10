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
- Stocks Universe: Stocks selected from the selection procedure

### Trading Strategy for each stock:

- For existing positions, if target hit:
    - Exit existing positions

- If RSI(7) > 70:
    - Execute a short order at current price and specified volume

- If RSI(7) < 30:
    - Execute a buy order at current price and specified volume


## Optimal Portfolio Parameters:

### Optimization Procedure
- Grid search with parameters:
(1) Max active positions per stock
(2) Stop Loss
(3) Profit Target
(4) Quantity of shares traded per order

- Aim to obtain parameters with positive P&Lm, low max drawdown and best Sharpe Ratio.


### Optimized Parameters
- Stop-Loss: None
- Profit-Taking Level: 6%
- Amount of shares per order: 10
- Maximum number of opened positions allowed: 50 * 16


### Result Statistics:
- Net Profit: $300300
- Annualized Return: 15.4%
- Sharpe Ratio: 1.17
- Max Drawdown: 0.248

### Cash Over Time
![alt text](https://github.com/yinkiatho/Quantmatter-Proj/main/Pictures/cot.png)


### Cumulative P&L Over Time
![alt text](https://github.com/yinkiatho/Quantmatter-Proj/main/Pictures/cumpnl.png)


