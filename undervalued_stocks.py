
import yfinance as yf

def get_undervalued_stocks():
    # Пример простого отбора акций по PE
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    undervalued = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe_ratio = info.get('trailingPE', None)
        if pe_ratio and pe_ratio < 20:  # Пример порога
            undervalued.append(f"{ticker} — P/E: {pe_ratio}")
    return undervalued
