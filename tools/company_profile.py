import yfinance as yf

def get_company_profile(ticker: str) -> dict:
    """
    Fetch company profile using yfinance.
    Returns a normalized dict or an error dict.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "symbol" not in info:
            return {
                "error": True,
                "message": f"No company found for ticker {ticker}"
            }

        return {
            "ticker": info.get("symbol", ticker),
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "N/A"),
            "exchange": info.get("exchange", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "website": info.get("website", "N/A"),
            "error": False
        }

    except Exception as e:
        return {"error": True, "message": f"Failed to fetch profile: {str(e)}"}
