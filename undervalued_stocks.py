import yfinance as yf

def weekly_undervalued_stocks_search(tickers):
    undervalued = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Метрики
            pe_ratio = info.get("trailingPE")
            peg_ratio = info.get("pegRatio")
            roe = info.get("returnOnEquity")
            current_ratio = info.get("currentRatio")
            debt_to_equity = info.get("debtToEquity")
            price_to_sales = info.get("priceToSalesTrailing12Months")
            price_to_book = info.get("priceToBook")
            return_on_capital = info.get("returnOnAssets")  # заменитель ROIC
            price_to_cashflow = info.get("operatingCashflow")
            free_cashflow = info.get("freeCashflow")
            market_price = info.get("previousClose")
            book_value = info.get("bookValue")
            earnings_per_share = info.get("trailingEps")

            # Graham Number = sqrt(22.5 * EPS * BV)
            if earnings_per_share and book_value:
                graham_number = (22.5 * earnings_per_share * book_value) ** 0.5
                graham_ratio = market_price / graham_number if graham_number else None
            else:
                graham_ratio = None

            # Earnings Yield = 1 / P/E
            earnings_yield = 1 / pe_ratio if pe_ratio else None

            # Margin of Safety: (Graham Number - Price) / Graham Number
            margin_of_safety = (graham_number - market_price) / graham_number if graham_ratio and graham_ratio < 1 else None

            # Фильтрация по метрикам
            if (
                margin_of_safety and margin_of_safety > 0.3 and
                peg_ratio is not None and peg_ratio < 1 and
                roe is not None and roe > 0.10 and
                current_ratio is not None and current_ratio > 1.5 and
                debt_to_equity is not None and debt_to_equity < 0.5 and
                earnings_yield is not None and earnings_yield > 0.03 and
                pe_ratio is not None and pe_ratio < 15 and
                price_to_sales is not None and price_to_sales < 1 and
                price_to_book is not None and price_to_book < 2 and
                return_on_capital is not None and return_on_capital > 0.20 and
                price_to_cashflow and free_cashflow and
                (market_price / (free_cashflow / info.get("sharesOutstanding", 1))) < 5 and
                graham_ratio is not None and graham_ratio < 1
            ):
                undervalued.append({
                    "ticker": ticker,
                    "P/E": pe_ratio,
                    "PEG": peg_ratio,
                    "ROE": roe,
                    "CR": current_ratio,
                    "D/E": debt_to_equity,
                    "P/S": price_to_sales,
                    "P/B": price_to_book,
                    "ROIC": return_on_capital,
                    "P/FCF": market_price / (free_cashflow / info.get("sharesOutstanding", 1)),
                    "Graham Ratio": graham_ratio,
                    "Margin of Safety": margin_of_safety
                })

        except Exception as e:
            print(f"[!] Ошибка при анализе {ticker}: {e}")

    return undervalued
