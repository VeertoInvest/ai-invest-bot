import yfinance as yf

def weekly_undervalued_stocks_search(tickers):
    undervalued = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Пример проверки по нескольким метрикам
            pe_ratio = info.get("trailingPE")
            peg_ratio = info.get("pegRatio")
            roe = info.get("returnOnEquity")
            current_ratio = info.get("currentRatio")
            debt_to_equity = info.get("debtToEquity")

            if (
                pe_ratio is not None and pe_ratio < 15 and
                peg_ratio is not None and peg_ratio < 1 and
                roe is not None and roe > 0.10 and
                current_ratio is not None and current_ratio > 1.5 and
                debt_to_equity is not None and debt_to_equity < 0.5
            ):
                undervalued.append({
                    "ticker": ticker,
                    "P/E": pe_ratio,
                    "PEG": peg_ratio,
                    "ROE": roe,
                    "CR": current_ratio,
                    "D/E": debt_to_equity
                })

        except Exception as e:
            print(f"[!] Ошибка при анализе {ticker}: {e}")

    return undervalued
