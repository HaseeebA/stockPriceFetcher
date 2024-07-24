# Stock Price Getter API

## Overview
The Stock Price Getter API is a Flask-based service that fetches current stock prices for specified tickers using the Yahoo Finance API (yfinance library). This API can be deployed on cloud platforms such as Google Cloud Run and can be utilized in various side projects requiring real-time stock price data.

## Features
- Fetches real-time stock prices.
- Caches stock prices to minimize redundant API calls.
- Supports a retry mechanism for failed fetch attempts.
- API key authentication for secure access.

## Prerequisites
- Docker
- A Docker Hub account
- Google Cloud account (if deploying to Google Cloud Run)

## Setup

### Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### Build and Push Docker Image
```bash
docker build -t stock-price-getter .
docker tag stock-price-getter <your-dockerhub-username>/stock_price_getter:latest
docker push <your-dockerhub-username>/stock_price_getter:latest
```

### Deploy to Google Cloud Run
1. Ensure you have the Google Cloud SDK installed and configured.
2. Deploy the container:
```bash
gcloud run deploy --image <your-dockerhub-username>/stock_price_getter:latest --platform managed
```

## Usage

### API Endpoint
`POST /prices`

### Headers
- `Content-Type: application/json`
- `X-API-Key: your-api-key`

### Request Body
```json
{
  "tickers": ["AAPL", "GOOGL", "MSFT"]
}
```

### Response
```json
{
  "AAPL": {"price": 150.25, "source": "cache"},
  "GOOGL": {"price": 2750.80, "source": "yfinance"},
  "MSFT": {"price": 300.10, "source": "yfinance"}
}
```

## Configuration
- Update the `api_keys.json` file with your desired API keys.
- Modify the caching duration in `app.py` if needed.

## Error Handling
- Invalid API key: Returns a 401 Unauthorized error.
- Missing or invalid request body: Returns a 400 Bad Request error.
- Failed to fetch stock price: Returns an error message in the response for the specific ticker.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
