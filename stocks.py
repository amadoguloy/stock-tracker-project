import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import yfinance as yf
import numpy as np
import requests
from textblob import TextBlob

# Initialize Dash app
app = dash.Dash(__name__)

# List of Top 20 Stocks by Market Cap (as of recent data)
top_20_stocks = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'BRK-B', 'META', 'V', 'JNJ',
    'WMT', 'JPM', 'PG', 'UNH', 'HD', 'DIS', 'PYPL', 'VZ', 'NFLX', 'LCID'
]

# Fetch Stock Data
def get_stock_data(ticker='AAPL', period='6mo'):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    hist.reset_index(inplace=True)
    
    # Calculate Indicators
    hist['MA50'] = hist['Close'].rolling(window=50).mean()
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    hist['Upper'] = hist['Close'].rolling(window=20).mean() + (hist['Close'].rolling(window=20).std() * 2)
    hist['Lower'] = hist['Close'].rolling(window=20).mean() - (hist['Close'].rolling(window=20).std() * 2)
    hist['RSI'] = 100 - (100 / (1 + hist['Close'].pct_change().rolling(14).mean()))
    return hist

# Fetch Sentiment Analysis Data
def get_stock_sentiment(ticker='AAPL'):
    url = f'https://finnhub.io/api/v1/news?category=general&token=YOUR_API_KEY'
    response = requests.get(url).json()
    sentiments = [TextBlob(article['headline']).sentiment.polarity for article in response if ticker in article['headline']]
    return np.mean(sentiments) if sentiments else 0

# Layout
app.layout = html.Div([
    html.H1("Advanced Stock Tracker", style={'textAlign': 'center'}),
    
    # Stock Selection
    html.H3("Select Stock"),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': ticker, 'value': ticker} for ticker in top_20_stocks],
        value='AAPL',
        clearable=False
    ),
    
    # Timeframe Selection
    html.H3("Select Timeframe"),
    dcc.RadioItems(
        id='timeframe-selector',
        options=[
            {'label': '1 Month', 'value': '1mo'},
            {'label': '6 Months', 'value': '6mo'},
            {'label': '1 Year', 'value': '1y'},
            {'label': '5 Years', 'value': '5y'}
        ],
        value='6mo',
        inline=True
    ),
    
    # Stock Graph
    dcc.Graph(id='stock-graph'),
    
    # Sentiment Analysis Output
    html.H3("Market Sentiment"),
    html.Div(id='sentiment-output'),
])

# Callback for updating stock graph
@app.callback(
    Output('stock-graph', 'figure'),
    [Input('stock-dropdown', 'value'), Input('timeframe-selector', 'value')]
)
def update_stock_chart(selected_stock, timeframe):
    df = get_stock_data(selected_stock, timeframe)
    fig = px.line(df, x='Date', y=['Close', 'Upper', 'Lower', 'MA50', 'MA200'],
                  title=f'{selected_stock} Stock Prices with Indicators')
    return fig

# Callback for sentiment analysis
@app.callback(
    Output('sentiment-output', 'children'),
    [Input('stock-dropdown', 'value')]
)
def update_sentiment(selected_stock):
    sentiment_score = get_stock_sentiment(selected_stock)
    sentiment_text = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
    return f'Sentiment Score: {sentiment_score:.2f} ({sentiment_text})'

# Run App
if __name__ == '__main__':
    app.run_server(debug=True)
