from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import time
import threading

app = Flask(__name__)
CORS(app)

CACHE_FILE = 'stock_cache.json'
API_KEYS_FILE = 'api_keys.json'

def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

API_KEYS = list(load_api_keys().values())

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.info['currentPrice']
        return price
    except Exception as e:
        print(e, f"Couldn't fetch price for {ticker} from yfinance.")
        return None

def is_cache_valid(timestamp, max_age=timedelta(hours=1)):
    return datetime.now() - datetime.fromisoformat(timestamp) < max_age

def should_retry(timestamp):
    return datetime.now() - datetime.fromisoformat(timestamp) > timedelta(days=1)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, default=str)

def update_cache():
    global cache
    while True:
        current_time = datetime.now()
        for ticker in list(cache.keys()):
            if 'error' in cache[ticker]:
                if should_retry(cache[ticker]['timestamp']):
                    price = get_stock_price(ticker)
                    if price is not None:
                        cache[ticker] = {'price': price, 'timestamp': current_time.isoformat()}
                    else:
                        cache[ticker] = {'error': 'Unable to fetch price', 'timestamp': current_time.isoformat()}
            else:
                price = get_stock_price(ticker)
                if price is not None:
                    cache[ticker] = {'price': price, 'timestamp': current_time.isoformat()}
                else:
                    cache[ticker] = {'error': 'Unable to fetch price', 'timestamp': current_time.isoformat()}
        save_cache(cache)
        time.sleep(1800)  # Wait for 1 minute

cache = load_cache()

update_thread = threading.Thread(target=update_cache, daemon=True)
update_thread.start()


print(API_KEYS)
@app.route('/prices', methods=['POST'])
def get_prices():
    api_key = request.headers.get('X-API-Key')
    if api_key not in API_KEYS:
        return jsonify({'error': 'Invalid API key'}), 401
    
    data = request.get_json()
    if not data or 'tickers' not in data:
        return jsonify({'error': 'No tickers provided'}), 400
    
    tickers = data['tickers']
    if not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400
    
    current_time = datetime.now()
    results = {}
    
    for ticker in tickers:
        ticker = ticker.upper()
        if ticker in cache:
            if 'error' in cache[ticker]:
                if should_retry(cache[ticker]['timestamp']):
                    price = get_stock_price(ticker)
                    if price is not None:
                        cache[ticker] = {'price': price, 'timestamp': current_time.isoformat()}
                        results[ticker] = {'price': price, 'source': 'yfinance'}
                    else:
                        cache[ticker] = {'error': 'Unable to fetch price', 'timestamp': current_time.isoformat()}
                        results[ticker] = {'error': 'Unable to fetch price'}
                else:
                    results[ticker] = {'error': 'Unable to fetch price', 'cached': True}
            elif is_cache_valid(cache[ticker]['timestamp']):
                results[ticker] = {'price': cache[ticker]['price'], 'source': 'cache'}
            else:
                price = get_stock_price(ticker)
                if price is not None:
                    cache[ticker] = {'price': price, 'timestamp': current_time.isoformat()}
                    results[ticker] = {'price': price, 'source': 'yfinance'}
                else:
                    cache[ticker] = {'error': 'Unable to fetch price', 'timestamp': current_time.isoformat()}
                    results[ticker] = {'error': 'Unable to fetch price'}
        else:
            price = get_stock_price(ticker)
            if price is not None:
                cache[ticker] = {'price': price, 'timestamp': current_time.isoformat()}
                results[ticker] = {'price': price, 'source': 'yfinance'}
            else:
                cache[ticker] = {'error': 'Unable to fetch price', 'timestamp': current_time.isoformat()}
                results[ticker] = {'error': 'Unable to fetch price'}
    
    save_cache(cache)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
# commands to run: 
# docker build -t stock-price-getter .
# docker tag stock-price-getter haseeeba/stock_price_getter:latest
# docker push haseeeba/stock_price_getter:latest