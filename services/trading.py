from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from decimal import Decimal
from typing import Dict, List, Optional

class TradingService:
    def __init__(self, alpaca_service):
        self.alpaca = alpaca_service

    def place_market_order(self, symbol: str, qty: float, side: str) -> Dict:
        """Place a market order"""
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        order = self.alpaca.client.submit_order(order_data)
        return self._format_order_response(order)

    def place_limit_order(self, symbol: str, qty: float, side: str, limit_price: float) -> Dict:
        """Place a limit order"""
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
        order = self.alpaca.client.submit_order(order_data)
        return self._format_order_response(order)

    def place_stop_order(self, symbol: str, qty: float, side: str, stop_price: float) -> Dict:
        """Place a stop order"""
        order_data = StopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            stop_price=stop_price
        )
        order = self.alpaca.client.submit_order(order_data)
        return self._format_order_response(order)

    def place_stop_limit_order(self, symbol: str, qty: float, side: str, stop_price: float, limit_price: float) -> Dict:
        """Place a stop-limit order"""
        order_data = StopLimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            stop_price=stop_price,
            limit_price=limit_price
        )
        order = self.alpaca.client.submit_order(order_data)
        return self._format_order_response(order)

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position details for a specific symbol"""
        try:
            position = self.alpaca.client.get_position(symbol)
            return {
                'symbol': position.symbol,
                'qty': float(position.qty),
                'market_value': float(position.market_value),
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc) * 100,
                'change_today': float(position.change_today) * 100
            }
        except Exception:
            return None

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders, optionally filtered by symbol"""
        orders = self.alpaca.client.get_orders(status='open', symbols=[symbol] if symbol else None)
        return [self._format_order_response(order) for order in orders]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        try:
            self.alpaca.client.cancel_order_by_id(order_id)
            return True
        except Exception:
            return False

    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            self.alpaca.client.cancel_orders()
            return True
        except Exception:
            return False

    def close_position(self, symbol: str) -> Dict:
        """Close a position for a specific symbol"""
        try:
            response = self.alpaca.client.close_position(symbol)
            return self._format_order_response(response)
        except Exception as e:
            return {'error': str(e)}

    def close_all_positions(self) -> bool:
        """Close all open positions"""
        try:
            self.alpaca.client.close_all_positions()
            return True
        except Exception:
            return False

    def get_asset_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed information about a tradable asset"""
        try:
            asset = self.alpaca.client.get_asset(symbol)
            return {
                'symbol': asset.symbol,
                'name': asset.name,
                'exchange': asset.exchange,
                'tradable': asset.tradable,
                'marginable': asset.marginable,
                'shortable': asset.shortable,
                'easy_to_borrow': asset.easy_to_borrow,
                'fractionable': asset.fractionable
            }
        except Exception:
            return None

    def get_clock(self) -> Dict:
        """Get the current market clock"""
        clock = self.alpaca.client.get_clock()
        return {
            'timestamp': clock.timestamp,
            'is_open': clock.is_open,
            'next_open': clock.next_open,
            'next_close': clock.next_close
        }

    def get_calendar(self, start: datetime, end: datetime) -> List[Dict]:
        """Get the market calendar between dates"""
        calendar = self.alpaca.client.get_calendar(start, end)
        return [{
            'date': day.date,
            'open': day.open,
            'close': day.close
        } for day in calendar]

    def _format_order_response(self, order) -> Dict:
        """Format order response into a standardized dictionary"""
        return {
            'id': order.id,
            'client_order_id': order.client_order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'type': order.type.value,
            'qty': float(order.qty) if order.qty else None,
            'filled_qty': float(order.filled_qty) if order.filled_qty else None,
            'status': order.status.value,
            'limit_price': float(order.limit_price) if order.limit_price else None,
            'stop_price': float(order.stop_price) if order.stop_price else None,
            'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
            'submitted_at': order.submitted_at,
            'filled_at': order.filled_at,
            'expired_at': order.expired_at,
            'canceled_at': order.canceled_at,
            'failed_at': order.failed_at,
            'replaced_at': order.replaced_at,
            'replaced_by': order.replaced_by,
            'replaces': order.replaces
        }
