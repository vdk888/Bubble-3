from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

class ChatbotActions:
    def __init__(self, trading_service, market_data_service, portfolio_service):
        self.trading = trading_service
        self.market_data = market_data_service
        self.portfolio = portfolio_service

    def handle_action(self, action: str, params: Dict[str, Any]) -> Dict:
        """Route the action to the appropriate handler"""
        action_handlers = {
            # Trading actions
            'place_market_order': self._place_market_order,
            'place_limit_order': self._place_limit_order,
            'place_stop_order': self._place_stop_order,
            'place_stop_limit_order': self._place_stop_limit_order,
            'cancel_order': self._cancel_order,
            'cancel_all_orders': self._cancel_all_orders,
            'close_position': self._close_position,
            'close_all_positions': self._close_all_positions,
            
            # Market data actions
            'get_quote': self._get_quote,
            'get_latest_trade': self._get_latest_trade,
            'get_bars': self._get_bars,
            'get_technical_analysis': self._get_technical_analysis,
            
            # Portfolio actions
            'get_portfolio_summary': self._get_portfolio_summary,
            'get_position_details': self._get_position_details,
            'get_open_orders': self._get_open_orders,
            'get_asset_info': self._get_asset_info,
            
            # Market status actions
            'get_market_status': self._get_market_status,
            'get_trading_calendar': self._get_trading_calendar
        }
        
        handler = action_handlers.get(action)
        if not handler:
            return {'error': f'Unknown action: {action}'}
            
        try:
            return handler(params)
        except Exception as e:
            return {'error': str(e)}

    # Trading action handlers
    def _place_market_order(self, params: Dict) -> Dict:
        """Place a market order"""
        required = ['symbol', 'qty', 'side']
        if not all(k in params for k in required):
            return {'error': f'Missing required parameters. Need: {", ".join(required)}'}
        
        return self.trading.place_market_order(
            symbol=params['symbol'].upper(),
            qty=float(params['qty']),
            side=params['side'].lower()
        )

    def _place_limit_order(self, params: Dict) -> Dict:
        """Place a limit order"""
        required = ['symbol', 'qty', 'side', 'limit_price']
        if not all(k in params for k in required):
            return {'error': f'Missing required parameters. Need: {", ".join(required)}'}
        
        return self.trading.place_limit_order(
            symbol=params['symbol'].upper(),
            qty=float(params['qty']),
            side=params['side'].lower(),
            limit_price=float(params['limit_price'])
        )

    def _place_stop_order(self, params: Dict) -> Dict:
        """Place a stop order"""
        required = ['symbol', 'qty', 'side', 'stop_price']
        if not all(k in params for k in required):
            return {'error': f'Missing required parameters. Need: {", ".join(required)}'}
        
        return self.trading.place_stop_order(
            symbol=params['symbol'].upper(),
            qty=float(params['qty']),
            side=params['side'].lower(),
            stop_price=float(params['stop_price'])
        )

    def _place_stop_limit_order(self, params: Dict) -> Dict:
        """Place a stop-limit order"""
        required = ['symbol', 'qty', 'side', 'stop_price', 'limit_price']
        if not all(k in params for k in required):
            return {'error': f'Missing required parameters. Need: {", ".join(required)}'}
        
        return self.trading.place_stop_limit_order(
            symbol=params['symbol'].upper(),
            qty=float(params['qty']),
            side=params['side'].lower(),
            stop_price=float(params['stop_price']),
            limit_price=float(params['limit_price'])
        )

    def _cancel_order(self, params: Dict) -> Dict:
        """Cancel a specific order"""
        if 'order_id' not in params:
            return {'error': 'Missing order_id parameter'}
        
        success = self.trading.cancel_order(params['order_id'])
        return {'success': success}

    def _cancel_all_orders(self, params: Dict) -> Dict:
        """Cancel all open orders"""
        success = self.trading.cancel_all_orders()
        return {'success': success}

    def _close_position(self, params: Dict) -> Dict:
        """Close a position for a specific symbol"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        return self.trading.close_position(params['symbol'].upper())

    def _close_all_positions(self, params: Dict) -> Dict:
        """Close all open positions"""
        success = self.trading.close_all_positions()
        return {'success': success}

    # Market data action handlers
    def _get_quote(self, params: Dict) -> Dict:
        """Get latest quote for a symbol"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        quote = self.market_data.get_latest_quote(params['symbol'].upper())
        if not quote:
            return {'error': 'Could not fetch quote'}
        return quote

    def _get_latest_trade(self, params: Dict) -> Dict:
        """Get latest trade for a symbol"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        trade = self.market_data.get_latest_trade(params['symbol'].upper())
        if not trade:
            return {'error': 'Could not fetch trade'}
        return trade

    def _get_bars(self, params: Dict) -> Dict:
        """Get historical bars for a symbol"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        timeframe = params.get('timeframe', '1D')
        limit = int(params.get('limit', 100))
        
        bars = self.market_data.get_bars(
            symbol=params['symbol'].upper(),
            timeframe=timeframe,
            limit=limit
        )
        return {'bars': bars}

    def _get_technical_analysis(self, params: Dict) -> Dict:
        """Get technical analysis for a symbol"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        bars = self.market_data.get_bars(
            symbol=params['symbol'].upper(),
            timeframe='1D',
            limit=200  # Need enough data for 200-day SMA
        )
        
        if not bars:
            return {'error': 'Could not fetch data for technical analysis'}
            
        indicators = self.market_data.calculate_technical_indicators(bars)
        return {
            'symbol': params['symbol'].upper(),
            'indicators': indicators
        }

    # Portfolio action handlers
    def _get_portfolio_summary(self, params: Dict) -> Dict:
        """Get portfolio summary"""
        return self.portfolio.get_portfolio_summary()

    def _get_position_details(self, params: Dict) -> Dict:
        """Get details for a specific position"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        position = self.trading.get_position(params['symbol'].upper())
        if not position:
            return {'error': 'Position not found'}
        return position

    def _get_open_orders(self, params: Dict) -> Dict:
        """Get open orders, optionally filtered by symbol"""
        symbol = params.get('symbol')
        if symbol:
            symbol = symbol.upper()
        
        orders = self.trading.get_open_orders(symbol)
        return {'orders': orders}

    def _get_asset_info(self, params: Dict) -> Dict:
        """Get asset information"""
        if 'symbol' not in params:
            return {'error': 'Missing symbol parameter'}
        
        info = self.trading.get_asset_info(params['symbol'].upper())
        if not info:
            return {'error': 'Asset not found'}
        return info

    # Market status action handlers
    def _get_market_status(self, params: Dict) -> Dict:
        """Get current market status"""
        return self.trading.get_clock()

    def _get_trading_calendar(self, params: Dict) -> Dict:
        """Get trading calendar"""
        start = datetime.now()
        end = start + timedelta(days=params.get('days', 7))
        
        calendar = self.trading.get_calendar(start, end)
        return {'calendar': calendar}

    def parse_natural_language(self, message: str) -> Optional[Dict]:
        """Parse natural language commands into structured actions"""
        # Trading commands
        buy_match = re.match(r'(?i)buy\s+(\d+)\s+(?:shares?\s+of\s+)?(\w+)', message)
        if buy_match:
            qty, symbol = buy_match.groups()
            return {
                'action': 'place_market_order',
                'params': {
                    'symbol': symbol,
                    'qty': float(qty),
                    'side': 'buy'
                }
            }

        sell_match = re.match(r'(?i)sell\s+(\d+)\s+(?:shares?\s+of\s+)?(\w+)', message)
        if sell_match:
            qty, symbol = sell_match.groups()
            return {
                'action': 'place_market_order',
                'params': {
                    'symbol': symbol,
                    'qty': float(qty),
                    'side': 'sell'
                }
            }

        # Quote requests
        quote_match = re.match(r'(?i)(?:get\s+)?quote\s+(?:for\s+)?(\w+)', message)
        if quote_match:
            symbol = quote_match.group(1)
            return {
                'action': 'get_quote',
                'params': {
                    'symbol': symbol
                }
            }

        # Position requests
        position_match = re.match(r'(?i)(?:get\s+)?position\s+(?:for\s+)?(\w+)', message)
        if position_match:
            symbol = position_match.group(1)
            return {
                'action': 'get_position_details',
                'params': {
                    'symbol': symbol
                }
            }

        # Portfolio summary request
        if re.match(r'(?i)(?:get\s+)?portfolio\s+summary', message):
            return {
                'action': 'get_portfolio_summary',
                'params': {}
            }

        # Technical analysis request
        ta_match = re.match(r'(?i)(?:get\s+)?(?:technical\s+analysis|indicators)\s+(?:for\s+)?(\w+)', message)
        if ta_match:
            symbol = ta_match.group(1)
            return {
                'action': 'get_technical_analysis',
                'params': {
                    'symbol': symbol
                }
            }

        # Market status request
        if re.match(r'(?i)(?:get\s+)?market\s+status', message):
            return {
                'action': 'get_market_status',
                'params': {}
            }

        return None
