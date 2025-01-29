# AlpacaService with Portfolio History Functions

from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderStatus, QueryOrderStatus
import os
from decimal import Decimal
from typing import Dict, List
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests

class AlpacaService:
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self._client = None
        self._data_client = None

    @property
    def client(self):
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca credentials not set. Please configure them in your account settings.")
        
        if self._client is None:
            self._client = TradingClient(self.api_key, self.secret_key, paper=True)
        return self._client

    @property
    def data_client(self):
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca credentials not set. Please configure them in your account settings.")
        
        if self._data_client is None:
            self._data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        return self._data_client

    def update_credentials(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self._client = None  # Force client recreation with new credentials
        self._data_client = None  # Force data client recreation with new credentials

    def get_account_info(self) -> dict:
        """Get current account information."""
        print("Getting account info from Alpaca...")
        try:
            account = self.client.get_account()
            
            # Convert Decimal values to float for JSON serialization
            account_info = {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'last_equity': float(account.last_equity),
                'day_change': float(account.equity) - float(account.last_equity),
                'day_change_percent': ((float(account.equity) - float(account.last_equity)) / float(account.last_equity)) * 100 if float(account.last_equity) != 0 else 0
            }
            
            print("Account info retrieved:", account_info)
            return account_info
            
        except Exception as e:
            print(f"Error getting account info: {str(e)}")
            raise

    def get_positions(self) -> List[Dict]:
        """Get current positions with latest market data."""
        positions = self.client.get_all_positions()
        positions_data = []
        
        for position in positions:
            market_value = float(position.market_value)
            cost_basis = float(position.cost_basis)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc) * 100  # Convert to percentage
            
            positions_data.append({
                'symbol': position.symbol,
                'qty': float(position.qty),
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pl': unrealized_pl,
                'unrealized_plpc': unrealized_plpc,
                'current_price': float(position.current_price),
                'avg_entry_price': float(position.avg_entry_price),
                'change_today': float(position.change_today) * 100  # Convert to percentage
            })
        
        return positions_data

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades/orders."""
        request_params = GetOrdersRequest(
            status=QueryOrderStatus.ALL,
            limit=limit,
            nested=True  # Include nested objects for more order details
        )
        print("ok")
        orders = self.client.get_orders(filter=request_params)
        trades = []
        
        for order in orders:
            trades.append({
                'symbol': order.symbol,
                'side': order.side.value,
                'qty': float(order.qty) if order.qty is not None else 0,
                'filled_qty': float(order.filled_qty) if order.filled_qty is not None else 0,
                'type': order.type.value,
                'status': order.status.value,
                'submitted_at': order.submitted_at,
                'filled_at': order.filled_at,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price is not None else 0,
            })
        return trades

    def calculate_asset_allocation(self, positions: List[Dict]) -> Dict:
        """Calculate asset allocation percentages."""
        total_value = sum(position['market_value'] for position in positions)
        allocation = {}
        
        if total_value > 0:
            for position in positions:
                allocation[position['symbol']] = (position['market_value'] / total_value) * 100
        
        return allocation
    
    def get_portfolio_history(self, timeframe='1D', period='1M', date_end=None):
        """Get historical portfolio values from Alpaca."""
        base_url = "https://paper-api.alpaca.markets"
        endpoint = f"{base_url}/v2/account/portfolio/history"
        
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        
        # Map the timeframe buttons to Alpaca's parameters
        params = {
            'extended_hours': 'true'
        }
        
        # Map timeframe selection to Alpaca's parameters
        if timeframe == "1D":
            params['timeframe'] = '1H'
            params['period'] = '1D'
        elif timeframe == "1W":
            params['timeframe'] = '1H'
            params['period'] = '1W'
        elif timeframe == "1M":
            params['timeframe'] = '1D'
            params['period'] = '1M'
        elif timeframe == "3M":
            params['timeframe'] = '1D'
            params['period'] = '3M'
        elif timeframe == "1Y":
            params['timeframe'] = '1D'
            params['period'] = '1A'
        else:  # ALL
            params['timeframe'] = '1D'
            params['period'] = 'all'
        
        if date_end:
            params['date_end'] = date_end
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error getting portfolio history: {response.text}")  # Debug print
            raise Exception(f"Error getting portfolio history: {response.text}")
        
        data = response.json()
        print(f"Portfolio history data: {data}")  # Debug print
        return data

    def create_portfolio_plot(self, portfolio_history):
        """Create a visualization of portfolio history."""
        timestamps = [datetime.fromtimestamp(ts) for ts in portfolio_history['timestamp']]
        
        plt.figure(figsize=(12, 6))
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
        fig.suptitle('Portfolio Performance', fontsize=16)
        
        ax1.plot(timestamps, portfolio_history['equity'], label='Portfolio Value', color='blue')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.grid(True)
        ax1.legend()
        
        locator = mdates.AutoDateLocator()
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        profit_loss_pct = portfolio_history['profit_loss_pct']
        ax2.plot(timestamps, profit_loss_pct, label='Profit/Loss %', color='green')
        ax2.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        ax2.set_ylabel('Profit/Loss %')
        ax2.grid(True)
        ax2.legend()
        
        ax2.xaxis.set_major_locator(locator)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        current_value = portfolio_history['equity'][-1]
        total_return = profit_loss_pct[-1]
        max_value = max(portfolio_history['equity'])
        min_value = min(portfolio_history['equity'])
        
        stats_text = f'Current Value: ${current_value:,.2f}\n'
        stats_text += f'Total Return: {total_return:.2f}%\n'
        stats_text += f'Max Value: ${max_value:,.2f}\n'
        stats_text += f'Min Value: ${min_value:,.2f}'
        
        ax1.text(0.02, 0.98, stats_text,
                transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf
