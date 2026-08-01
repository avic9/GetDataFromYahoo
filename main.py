from GetDataFromYahoo import get_current_price

def main():
    ticker = "BAC"
    try:
        price = get_current_price(ticker)
        print(f"Current price for {ticker}: {price}")
    except Exception as e:
        print(f"Error retrieving price for {ticker}: {e}")

if __name__ == "__main__":
    main()


