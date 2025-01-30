import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class PerformanceAnalysisService:
    def __init__(self):
        # Common benchmarks
        self.benchmarks = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ-100',
            'IWM': 'Russell 2000',
            'AGG': 'US Aggregate Bond'
        }
        
    def get_performance_comparison(self, positions: List[Dict], timeframes: List[str] = ['1d', '1mo', '3mo', '1y']) -> Dict:
        """Get detailed performance analysis with benchmark comparisons"""
        # Get position symbols and their weights
        total_value = sum(pos['market_value'] for pos in positions)
        portfolio_weights = {pos['symbol']: pos['market_value'] / total_value for pos in positions}
        
        # Initialize results
        results = {
            'portfolio_performance': {},
            'asset_performance': {},
            'benchmark_comparison': {},
            'timeframes_analyzed': timeframes
        }
        
        # Get performance for each asset
        for pos in positions:
            symbol = pos['symbol']
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1y')  # Get 1y of data to cover all timeframes
            
            results['asset_performance'][symbol] = {
                'weight': portfolio_weights[symbol],
                'performance': {}
            }
            
            for timeframe in timeframes:
                perf = self._calculate_period_performance(hist, timeframe)
                results['asset_performance'][symbol]['performance'][timeframe] = perf
        
        # Get benchmark performance
        for symbol, name in self.benchmarks.items():
            benchmark = yf.Ticker(symbol)
            hist = benchmark.history(period='1y')
            
            results['benchmark_comparison'][symbol] = {
                'name': name,
                'performance': {}
            }
            
            for timeframe in timeframes:
                perf = self._calculate_period_performance(hist, timeframe)
                results['benchmark_comparison'][symbol]['performance'][timeframe] = perf
        
        # Calculate portfolio performance for each timeframe
        for timeframe in timeframes:
            portfolio_return = sum(
                results['asset_performance'][symbol]['performance'][timeframe] * weight
                for symbol, weight in portfolio_weights.items()
            )
            results['portfolio_performance'][timeframe] = portfolio_return
        
        return results
    
    def _calculate_period_performance(self, history: pd.DataFrame, timeframe: str) -> float:
        """Calculate performance for a specific timeframe"""
        if history.empty:
            return 0.0
            
        end_price = history['Close'][-1]
        
        if timeframe == '1d':
            start_price = history['Open'][-1]
        else:
            periods = {
                '1mo': 21,
                '3mo': 63,
                '1y': 252
            }
            lookback = periods.get(timeframe, 21)
            if len(history) >= lookback:
                start_price = history['Close'][-lookback]
            else:
                start_price = history['Close'][0]
        
        return ((end_price / start_price) - 1) * 100 