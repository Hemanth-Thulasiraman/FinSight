import yfinance as yf

def get_financial_data(ticker: str) -> dict:
    """
    Fetch key financial metrics for a company using yfinance.
    Returns a normalized dict or an error dict.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            return {
                "error": True,
                "message": f"No financial data found for {ticker}"
            }

        return {
            "ticker": ticker,
            "revenue": info.get("totalRevenue", None),
            "gross_margins": info.get("grossMargins", None),
            "operating_margins": info.get("operatingMargins", None),
            "profit_margins": info.get("profitMargins", None),
            "earnings_per_share": info.get("trailingEps", None),
            "pe_ratio": info.get("trailingPE", None),
            "debt_to_equity": info.get("debtToEquity", None),
            "return_on_equity": info.get("returnOnEquity", None),
            "free_cash_flow": info.get("freeCashflow", None),
            "52_week_high": info.get("fiftyTwoWeekHigh", None),
            "52_week_low": info.get("fiftyTwoWeekLow", None),
            "error": False
        }

    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to fetch financial data: {str(e)}"
        }

