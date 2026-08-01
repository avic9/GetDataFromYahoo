import argparse
import os
from datetime import datetime
from pathlib import Path

from price_target_service import build_report, load_rows_from_xml, save_rows_to_xml, send_email_report, update_rows_from_yahoo


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the price target workflow")
    parser.add_argument("--ticker", action="append", default=[], help="Ticker to include; can be used multiple times")
    parser.add_argument("--email", default=os.getenv("EMAIL_TO"), help="Recipient email override")
    parser.add_argument("--xml-path", default=None, help="Optional path to the XML input file")
    args = parser.parse_args()

    rows = load_rows_from_xml(Path(args.xml_path) if args.xml_path else None)
    if args.ticker:
        rows = [{"TickerName": ticker, "TargetPrice": "", "CurrentPrice": "", "PERatio": "", "ROIC": ""} for ticker in args.ticker]

    updated_rows = update_rows_from_yahoo(rows)
    xml_path = save_rows_to_xml(updated_rows, Path(args.xml_path) if args.xml_path else None)

    report = build_report(updated_rows)
    print("\n" + report)

    subject = f"Price Target Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_email_report(subject, report, args.email)

    print(f"\nSaved XML report to {xml_path}")
    return 0


if __name__ == "__main__":
    main()
