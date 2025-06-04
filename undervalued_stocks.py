import yfinance as yf
import pandas as pd

def analyze_undervalued_stocks():
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    messages = []

    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe_ratio = info.get("trailingPE", None)

        if pe_ratio and pe_ratio < 20:
            messages.append(f"{ticker}: P/E = {pe_ratio}")

    if not messages:
        return "Не найдено недооцененных акций."

    return "📉 Недооцененные акции:
" + "\n".join(messages)