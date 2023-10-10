from portfolio import PortfolioTrader

import pandas as pd
import numpy as np


def grid_search_optimizer():
    
    stop_losses = [10000]
    max_active_positions = [6, 8, 10, 12, 14, 16]
    quantities = [15, 25, 35, 10, 20, 30]
    targets = [0.03, 0.02, 0.04, 0.05, 0.06]
    
    
    #stop_losses = [10000]
    #max_active_positions = [10, 20]
    #quantities = [10]
    #targets = [0.03]
    
    # Results of the grid search
    metrics = pd.DataFrame(columns=['Stop Loss', 'Quantity Shares Traded', 'Max Active Positions', 'Target',
                                    'Sharpe Ratio', 'Max Drawdown', 'Annualized return', 'PnL'])
    for target in targets:
        for stop_loss in stop_losses:
            for max_active_position in max_active_positions:
                for quantity in quantities:
                    if target < stop_loss and stop_loss != 10000:
                        continue
                    portfolio = PortfolioTrader(quantity=quantity, max_active_positions=50 *max_active_position, stop_loss=stop_loss, target=target)
                    portfolio.simulate()
                    portfolio.calculate_metrics()
                    #print(portfolio.metrics)
                    print(portfolio.metrics.head(1))
                
                    metrics = pd.concat([metrics, portfolio.metrics], axis=0, ignore_index=True)
                    #print(metrics)
                    
                    
                    
                
    # Filter out the results with negative PnL and sort by Sharpe Ratio
    #print(metrics)
    metrics = metrics.loc[metrics['PnL'] >= 0]
    metrics.sort_values(by='Sharpe Ratio', ascending=False, inplace=True, ignore_index=True)
    
    #Plot results
    print("Grid Search Results")
    
    print(metrics.head(10))
    
    # (stop_loss, quantity, max_active_positions, )
    stop_loss, quantity, max_active_positions, target = metrics.iloc[0, 0], metrics.iloc[0, 1], metrics.iloc[0, 2], metrics.iloc[0, 3]
    print("Best Parameters Found: " + str(stop_loss) + " " + str(quantity) + " " + str(max_active_positions) + " " + str(target))
    return (stop_loss, quantity, max_active_positions, target)

                

if __name__ == '__main__':
    #'''
    print("Starting Grid Search Optimizer")
    stop_loss, quantity, max_active_positions, target = grid_search_optimizer()
    
    print("Best Parameters Found: ")
    print("Stop Loss: ", stop_loss)
    print("Quantity Shares Traded: ", quantity)
    print("Max Active Positions: ", max_active_positions)
    print("Target: ", target)
    #'''
    #Grid Search Optimizer for the best parameters, max_active_positions and stop_loss

    portfolio = PortfolioTrader(quantity=quantity, max_active_positions=50 * max_active_positions, stop_loss=stop_loss,
                                target=target)
    #portfolio = PortfolioTrader(quantity=10, max_active_positions=50 * 6, stop_loss=10000,
    #                            target=0.03)
    portfolio.simulate()
    portfolio.calculate_metrics()
    print(portfolio.metrics)
    portfolio.print_summary()
    
    portfolio.plot_cash()
    portfolio.plot_profit() 
    #print(sum(list(portfolio.PnL.values())))
    
