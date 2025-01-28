from datetime import datetime, timedelta
import os
import sys

# Get the parent directory path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from alpaca_service.alpaca_service import AlpacaService

class PortfolioService:
    def __init__(self):
        self.alpaca = AlpacaService()
        self.account_info = None
        self.positions = None
        self.portfolio_history = None

    def initialize_with_credentials(self, api_key, secret_key):
        """Initialize the service with user credentials"""
        self.alpaca.update_credentials(api_key, secret_key)
        self.refresh_data()

    def refresh_data(self):
        """Refresh all portfolio data from Alpaca"""
        self.account_info = self.alpaca.get_account_info()
        self.positions = self.alpaca.get_positions()
        self.portfolio_history = self.alpaca.get_portfolio_history()

    def get_portfolio_summary(self):
        """Get the main portfolio metrics"""
        if not self.account_info:
            raise ValueError("Portfolio not initialized. Please configure Alpaca credentials.")
            
        return {
            'type': 'metrics',
            'metrics': {
                'Total Value': f"${self.account_info['portfolio_value']:,.2f}",
                'Daily Change': f"{self.account_info['day_change_percent']:+.2f}%",
                'Cash Available': f"${self.account_info['cash']:,.2f}",
                'Buying Power': f"${self.account_info['buying_power']:,.2f}"
            }
        }

    def get_asset_allocation(self):
        """Get asset allocation chart data"""
        if not self.account_info:
            raise ValueError("Portfolio not initialized. Please configure Alpaca credentials.")
            
        # Calculate total portfolio value and cash percentage
        total_value = self.account_info['portfolio_value']
        cash_value = self.account_info['cash']
        
        # Prepare data for the chart
        assets = []
        colors = []
        
        # Add positions
        position_colors = {
            0: '#4CAF50',   # Green
            1: '#2196F3',   # Blue
            2: '#FFC107',   # Yellow
            3: '#9E9E9E',   # Grey
            'default': '#673AB7'  # Purple for additional positions
        }
        
        for i, position in enumerate(self.positions):
            assets.append({
                'name': position['symbol'],
                'value': position['market_value']
            })
            colors.append(position_colors.get(i, position_colors['default']))
        
        # Add cash if it's significant (more than 1% of portfolio)
        if cash_value / total_value > 0.01:
            assets.append({
                'name': 'Cash',
                'value': cash_value
            })
            colors.append('#9E9E9E')  # Grey for cash

        return {
            'type': 'chart',
            'config': {
                'type': 'doughnut',
                'data': {
                    'labels': [asset['name'] for asset in assets],
                    'datasets': [{
                        'data': [asset['value'] for asset in assets],
                        'backgroundColor': colors
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': 'Asset Allocation'
                        }
                    }
                }
            }
        }

    def get_performance_chart(self):
        """Get historical performance chart data"""
        if not self.portfolio_history:
            raise ValueError("Portfolio not initialized. Please configure Alpaca credentials.")
            
        timestamps = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') 
                     for ts in self.portfolio_history['timestamp']]
        equity_values = self.portfolio_history['equity']
        
        return {
            'type': 'chart',
            'config': {
                'type': 'line',
                'data': {
                    'labels': timestamps,
                    'datasets': [{
                        'label': 'Portfolio Value',
                        'data': equity_values,
                        'borderColor': '#4CAF50',
                        'tension': 0.4
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'position': 'top',
                        },
                        'title': {
                            'display': True,
                            'text': 'Portfolio Performance'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': False,
                            'ticks': {
                                'format': { 'style': 'currency', 'currency': 'USD' }
                            }
                        }
                    }
                }
            }
        }

    def get_portfolio_history(self):
        """Get portfolio performance history data"""
        if not self.portfolio_history:
            raise ValueError("Portfolio not initialized. Please configure Alpaca credentials.")
            
        print("Portfolio history data:", self.portfolio_history)
        
        # Calculate today's return
        today_return = self.portfolio_history['profit_loss_pct'][-1] * 100 if self.portfolio_history['profit_loss_pct'] else 0
        
        # Calculate total return
        total_return = ((self.portfolio_history['equity'][-1] - self.portfolio_history['base_value']) / self.portfolio_history['base_value']) * 100 if self.portfolio_history['equity'] else 0
        
        return {
            'today_return': today_return,
            'total_return': total_return,
            'history': {
                'timestamps': [datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') for ts in self.portfolio_history['timestamp']],
                'equity': self.portfolio_history['equity']
            }
        }

    def get_recent_trades(self):
        """Get recent trades"""
        try:
            trades = self.alpaca.get_recent_trades()
            return [{
                'symbol': trade['symbol'],
                'side': trade['side'],
                'qty': trade['filled_qty'],
                'price': trade['filled_avg_price'],
                'timestamp': trade['filled_at'].strftime('%Y-%m-%d %H:%M:%S') if trade['filled_at'] else trade['submitted_at'].strftime('%Y-%m-%d %H:%M:%S')
            } for trade in trades if trade['status'] == 'filled']
        except Exception as e:
            print(f"Error getting trades: {str(e)}")
            return []
