"""
Portfolio history functionality for Alpaca trading account
"""

import io
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY

def get_portfolio_history(timeframe='1D', period='1M', date_end=None):
    """
    Get historical portfolio values from Alpaca
    
    Args:
        timeframe (str): Time between data points ('1Min', '5Min', '15Min', '1H', '1D')
        period (str): Length of time window ('1D', '1M', '3M', '1A')
        date_end (str): End date for the data (format: YYYY-MM-DD)
    
    Returns:
        dict: Portfolio history data including equity values and timestamps
    """
    # API endpoint (using paper trading by default)
    base_url = "https://paper-api.alpaca.markets"
    endpoint = f"{base_url}/v2/account/portfolio/history"
    
    # Headers for authentication
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    
    # Convert timeframe to period if needed
    timeframe_map = {
        '1Min': '1Min',
        '5Min': '5Min',
        '15Min': '15Min',
        '1H': '1Hour',
        '1D': '1D'
    }
    
    period_map = {
        '1D': '1D',
        '1W': '1W',
        '1M': '1M',
        '3M': '3M',
        '1A': '1A'
    }
    
    # Parameters for the request
    params = {
        'timeframe': timeframe_map.get(timeframe, timeframe),
        'period': period_map.get(period, period),
        'extended_hours': 'true'
    }
    
    if date_end:
        params['date_end'] = date_end
    
    # Make the request
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error getting portfolio history: {response.text}")
    
    return response.json()

def create_portfolio_plot(portfolio_history):
    """
    Create a visualization of portfolio history from Alpaca data
    
    Args:
        portfolio_history (dict): Portfolio history data from get_portfolio_history()
    
    Returns:
        bytes: PNG image data as bytes buffer
    """
    # Convert timestamps to datetime
    timestamps = [datetime.fromtimestamp(ts) for ts in portfolio_history['timestamp']]
    
    # Create figure and axis
    plt.figure(figsize=(12, 6))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    fig.suptitle('Portfolio Performance', fontsize=16)
    
    # Plot equity line
    ax1.plot(timestamps, portfolio_history['equity'], label='Portfolio Value', color='blue')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.grid(True)
    ax1.legend()
    
    # Format x-axis based on timeframe
    locator = mdates.AutoDateLocator()
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot profit/loss percentage
    profit_loss_pct = portfolio_history['profit_loss_pct']
    ax2.plot(timestamps, profit_loss_pct, label='Profit/Loss %', color='green')
    ax2.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    ax2.set_ylabel('Profit/Loss %')
    ax2.grid(True)
    ax2.legend()
    
    # Format x-axis for profit/loss subplot
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add some statistics as text
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
    
    # Adjust layout
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf
