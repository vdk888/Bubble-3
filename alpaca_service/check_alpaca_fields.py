import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_SECRET_KEY')

def explore_alpaca_data():
    """Explore available data fields from Alpaca"""
    try:
        # Initialize trading client
        trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
        
        # Get account information
        account = trading_client.get_account()
        print("\nAccount Fields:")
        print("-" * 50)
        for field in dir(account):
            if not field.startswith('_'):  # Skip private attributes
                value = getattr(account, field)
                if not callable(value):  # Skip methods
                    print(f"{field}: {value}")

        # Get sample asset information
        print("\nAsset Fields (using SPY as example):")
        print("-" * 50)
        asset = trading_client.get_asset('SPY')
        for field in dir(asset):
            if not field.startswith('_'):
                value = getattr(asset, field)
                if not callable(value):
                    print(f"{field}: {value}")

        # Get positions information
        print("\nPosition Fields (if any positions exist):")
        print("-" * 50)
        try:
            positions = trading_client.get_all_positions()
            if positions:
                for field in dir(positions[0]):
                    if not field.startswith('_'):
                        value = getattr(positions[0], field)
                        if not callable(value):
                            print(f"{field}: {value}")
            else:
                print("No open positions found")
        except Exception as e:
            print(f"No position data available: {str(e)}")

    except Exception as e:
        logger.error(f"Error exploring Alpaca data: {str(e)}")
        raise

if __name__ == "__main__":
    explore_alpaca_data()
