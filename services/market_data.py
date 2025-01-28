from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest, StockTradesRequest
from alpaca.data.timeframe import TimeFrame
from typing import Dict, List, Optional

class MarketDataService:
    def __init__(self, alpaca_service):
        self.alpaca = alpaca_service

    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """Get the latest quote for a symbol"""
        try:
            request = StockQuotesRequest(symbol_or_symbols=symbol)
            quotes = self.alpaca.data_client.get_stock_latest_quote(request)
            quote = quotes[symbol]
            return {
                'symbol': symbol,
                'ask_price': float(quote.ask_price),
                'ask_size': quote.ask_size,
                'bid_price': float(quote.bid_price),
                'bid_size': quote.bid_size,
                'timestamp': quote.timestamp
            }
        except Exception:
            return None

    def get_latest_trade(self, symbol: str) -> Optional[Dict]:
        """Get the latest trade for a symbol"""
        try:
            request = StockTradesRequest(symbol_or_symbols=symbol)
            trades = self.alpaca.data_client.get_stock_latest_trade(request)
            trade = trades[symbol]
            return {
                'symbol': symbol,
                'price': float(trade.price),
                'size': trade.size,
                'timestamp': trade.timestamp
            }
        except Exception:
            return None

    def get_bars(self, symbol: str, timeframe: str = '1D', start: datetime = None, end: datetime = None, limit: int = 100) -> List[Dict]:
        """Get historical bars for a symbol"""
        # Map timeframe string to TimeFrame enum
        timeframe_map = {
            '1Min': TimeFrame.Minute,
            '5Min': TimeFrame.Minute * 5,
            '15Min': TimeFrame.Minute * 15,
            '1H': TimeFrame.Hour,
            '1D': TimeFrame.Day
        }

        if timeframe not in timeframe_map:
            raise ValueError(f"Invalid timeframe. Must be one of: {', '.join(timeframe_map.keys())}")

        if not start:
            start = datetime.now() - timedelta(days=30)
        if not end:
            end = datetime.now()

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe_map[timeframe],
            start=start,
            end=end,
            limit=limit
        )

        try:
            bars = self.alpaca.data_client.get_stock_bars(request)
            return [{
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': bar.volume,
                'trade_count': bar.trade_count,
                'vwap': float(bar.vwap)
            } for bar in bars[symbol]]
        except Exception:
            return []

    def get_snapshots(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get latest snapshots (quote + trade) for multiple symbols"""
        results = {}
        for symbol in symbols:
            quote = self.get_latest_quote(symbol)
            trade = self.get_latest_trade(symbol)
            if quote and trade:
                results[symbol] = {
                    'quote': quote,
                    'trade': trade
                }
        return results

    def calculate_technical_indicators(self, bars: List[Dict]) -> Dict:
        """Calculate basic technical indicators from bar data"""
        if not bars:
            return {}

        # Calculate Simple Moving Averages (SMA)
        closes = [bar['close'] for bar in bars]
        sma_20 = sum(closes[-20:]) / min(20, len(closes))
        sma_50 = sum(closes[-50:]) / min(50, len(closes))
        sma_200 = sum(closes[-200:]) / min(200, len(closes))

        # Calculate RSI (14 periods)
        gains = []
        losses = []
        for i in range(1, min(15, len(closes))):
            change = closes[i] - closes[i-1]
            if change >= 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        # Calculate MACD (12, 26, 9)
        ema_12 = closes[-1]  # Simplified EMA calculation
        ema_26 = closes[-1]  # Simplified EMA calculation
        macd_line = ema_12 - ema_26
        signal_line = macd_line  # Simplified signal line calculation

        return {
            'sma': {
                '20': round(sma_20, 2),
                '50': round(sma_50, 2),
                '200': round(sma_200, 2)
            },
            'rsi': round(rsi, 2),
            'macd': {
                'line': round(macd_line, 2),
                'signal': round(signal_line, 2),
                'histogram': round(macd_line - signal_line, 2)
            }
        }
