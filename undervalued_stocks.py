import yfinance as yf

def find_undervalued_stocks(tickers):
    undervalued = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        try:
            info = stock.info
            pe_ratio = info.get("trailingPE", None)
            if pe_ratio and pe_ratio < 15:
                undervalued.append((ticker, pe_ratio))
        except Exception as e:
            print(f"Ошибка при обработке {ticker}: {e}")
    return undervalued
