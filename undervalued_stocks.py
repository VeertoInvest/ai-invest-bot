import yfinance as yf

def weekly_undervalued_stocks_search(tickers):
    undervalued = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Извлекаем метрики
            pe_ratio = info.get("trailingPE")
            peg_ratio = info.get("pegRatio")
            roe = info.get("returnOnEquity")
            current_ratio = info.get("currentRatio")
            debt_to_equity = info.get("debtToEquity")
            price_to_sales = info.get("priceToSalesTrailing12Months")
            price_to_book = info.get("priceToBook")
            return_on_assets = info.get("returnOnAssets")  # суррогат ROIC
            price = info.get("previousClose")
            eps = info.get("trailingEps")
            book_value = info.get("bookValue")
            free_cashflow = info.get("freeCashflow")
            shares_outstanding = info.get("sharesOutstanding") or 1  # защита от деления на 0

            # Рассчитываем Graham Number
            graham_number = (22.5 * eps * book_value) ** 0.5 if eps and book_value else None
            graham_ratio = price / graham_number if graham_number else None

            # Earnings yield
            earnings_yield = 1 / pe_ratio if pe_ratio else None

            # Margin of Safety
            margin_of_safety = (graham_number - price) / graham_number if graham_ratio and graham_ratio < 1 else None

            # P/Free Cash Flow
            p_fcf_ratio = (price * shares_outstanding) / free_cashflow if free_cashflow else None

            # Условия отбора
            if all([
                margin_of_safety and margin_of_safety >= 0.3,
                peg_ratio is not None and peg_ratio < 1,
                roe is not None and roe >= 0.10,
                current_ratio is not None and current_ratio >= 1.5,
                debt_to_equity is not None and debt_to_equity < 0.5,
                earnings_yield is not None and earnings_yield > 0.03,
                pe_ratio is not None and pe_ratio < 15,
                price_to_sales is not None and price_to_sales < 1,
                price_to_book is not None and price_to_book < 2,
                return_on_assets is not None and return_on_assets > 0.20,
                p_fcf_ratio is not None and p_fcf_ratio < 5,
                graham_ratio is not None and graham_ratio < 1
            ]):
                undervalued.append({
                    "ticker": ticker,
                    "P/E": round(pe_ratio, 2),
                    "PEG": round(peg_ratio, 2),
                    "ROE": round(roe, 2),
                    "Current Ratio": round(current_ratio, 2),
                    "D/E": round(debt_to_equity, 2),
                    "P/S": round(price_to_sales, 2),
                    "P/B": round(price_to_book, 2),
                    "ROIC": round(return_on_assets, 2),
                    "P/FCF": round(p_fcf_ratio, 2),
                    "Graham Ratio": round(graham_ratio, 2),
                    "Margin of Safety": f"{round(margin_of_safety * 100, 1)}%"
                })

        except Exception as e:
            print(f"[⚠️] Ошибка при анализе {ticker}: {e}")

    return undervalued
