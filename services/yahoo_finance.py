import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging

class YahooFinanceService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_price_data(
        self, 
        symbols: Union[str, List[str]], 
        timeframe: str = '1mo',
        interval: str = '1d'
    ) -> Dict:
        """
        Fetch price data from Yahoo Finance
        
        Args:
            symbols: Single symbol or list of symbols
            timeframe: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            Dictionary containing price data and metadata for each symbol
        """
        try:
            # Convert single symbol to list
            if isinstance(symbols, str):
                symbols = [symbols]

            result = {}
            
            for symbol in symbols:
                self.logger.info(f"Fetching data for {symbol}")
                try:
                    # Get ticker info
                    ticker = yf.Ticker(symbol)
                    
                    # Get historical data
                    hist = ticker.history(period=timeframe, interval=interval)
                    
                    if hist.empty:
                        self.logger.warning(f"No data found for {symbol}")
                        continue
                    
                    # Get basic info
                    info = ticker.info
                    
                    # Format the data
                    price_data = {
                        'prices': hist.to_dict('records'),
                        'metadata': {
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'currency': info.get('currency', 'USD'),
                            'exchange': info.get('exchange', 'Unknown'),
                            'current_price': info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else None),
                            'market_cap': info.get('marketCap'),
                            'sector': info.get('sector'),
                            'industry': info.get('industry')
                        },
                        'timeframe': timeframe,
                        'interval': interval,
                        'start_date': hist.index[0].isoformat() if not hist.empty else None,
                        'end_date': hist.index[-1].isoformat() if not hist.empty else None
                    }
                    
                    result[symbol] = price_data
                    self.logger.info(f"Successfully fetched data for {symbol}")
                    
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    result[symbol] = {'error': str(e)}

            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_price_data: {str(e)}")
            return {'error': str(e)}

    def get_market_summary(self) -> Dict:
        """Get summary of major market indices"""
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']
        return self.get_price_data(indices, timeframe='1d', interval='1m')

    def get_company_info(self, symbol: str) -> Dict:
        """Get detailed company information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'basic_info': {
                    'name': info.get('shortName'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'country': info.get('country'),
                    'website': info.get('website'),
                    'description': info.get('longBusinessSummary')
                },
                'financial_info': {
                    'market_cap': info.get('marketCap'),
                    'forward_pe': info.get('forwardPE'),
                    'dividend_yield': info.get('dividendYield'),
                    'beta': info.get('beta'),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting company info for {symbol}: {str(e)}")
            return {'error': str(e)} 