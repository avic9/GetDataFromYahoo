import sys

try:
    import yfinance as yf
except ImportError:
    print("yfinance library not found. Please install it using 'pip install yfinance'.")
    sys.exit(1)

def get_current_price(ticker_symbol: str) -> float:
    """
    Returns the current price for the given ticker symbol.
    """
    stock = yf.Ticker(ticker_symbol)
    financials = stock.financials
    print("\nFinancials:")
    print(financials)
    return stock.fast_info.last_price

def get_current_pe_ratio(ticker_symbol: str) -> float:
    """
    Returns the current P/E ratio for the given ticker symbol.
    """
    stock = yf.Ticker(ticker_symbol)
    return stock.info.get('trailingPE')



def get_current_roic(ticker_symbol: str) -> float:

    """
    Returns the current ROIC ratio for the given ticker symbol.
    """
    stock = yf.Ticker(ticker_symbol)

    # 2. Fetch trailing twelve months (TTM) financial data
    income_stmt = stock.quarterly_income_stmt
    balance_sheet = stock.quarterly_balance_sheet

    # 3. Extract relevant values (simplifying to TTM / recent quarter for example)
    # (Note: In production, you would sum the last 4 quarters for Operating Income and use Average Invested Capital)
    operating_income = income_stmt.loc['OperatingIncome'].iloc[0]
    tax_rate = 0.21  # Standard US corporate tax assumption (or dynamically compute from tax expenses)
    nopat = operating_income * (1 - tax_rate)

    total_debt = balance_sheet.loc['TotalLiabilitiesNetMinorityInterest'].iloc[0] - balance_sheet.loc['CurrentLiabilities'].iloc[0] # Approximating
    total_equity = balance_sheet.loc['StockholdersEquity'].iloc[0]
    cash = balance_sheet.loc['CashAndCashEquivalents'].iloc[0]

    invested_capital = total_debt + total_equity - cash

    # 4. Calculate ROIC
    roic = (nopat / invested_capital) * 100
    print(f"{ticker_symbol} ROIC: {roic:.2f}%")
    return roic
