import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

import yfinance as yf


DEFAULT_TICKERS = ["AAPL", "MSFT", "BAC", "NVDA"]
DEFAULT_DATA_DIR = Path("price_target_output")
DEFAULT_XML_PATH = DEFAULT_DATA_DIR / "price_targets.xml"


def get_data_dir() -> Path:
    configured = os.getenv("PRICE_TARGET_DATA_DIR")
    if configured:
        return Path(configured)
    return DEFAULT_DATA_DIR


def get_xml_path() -> Path:
    configured = os.getenv("PRICE_TARGET_XML_PATH")
    if configured:
        return Path(configured)
    return get_data_dir() / "price_targets.xml"


def get_default_rows() -> List[Dict[str, Any]]:
    return [
        {"TickerName": ticker, "TargetPrice": "", "CurrentPrice": "", "PERatio": "", "ROIC": ""}
        for ticker in DEFAULT_TICKERS
    ]


def load_rows_from_xml(xml_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    if xml_path is None:
        xml_path = get_xml_path()

    if not xml_path.exists():
        return get_default_rows()

    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(xml_path)
        root = tree.getroot()
        rows: List[Dict[str, Any]] = []
        for entry_elem in root.findall("Entry"):
            rows.append(
                {
                    "TickerName": entry_elem.get("TickerName", ""),
                    "TargetPrice": entry_elem.get("TargetPrice", ""),
                    "CurrentPrice": entry_elem.get("CurrentPrice", ""),
                    "PERatio": entry_elem.get("PERatio", ""),
                    "ROIC": entry_elem.get("ROIC", ""),
                }
            )
        if rows:
            return rows
    except Exception as exc:
        print(f"Warning: unable to read XML data: {exc}")

    return get_default_rows()


def save_rows_to_xml(rows: List[Dict[str, Any]], xml_path: Optional[Path] = None) -> Path:
    if xml_path is None:
        xml_path = get_xml_path()

    xml_path.parent.mkdir(parents=True, exist_ok=True)
    import xml.etree.ElementTree as ET

    root = ET.Element("PriceTargets")
    for row in rows:
        if not any(str(value).strip() for value in row.values()):
            continue
        entry_elem = ET.SubElement(root, "Entry")
        entry_elem.set("TickerName", row.get("TickerName", ""))
        entry_elem.set("TargetPrice", row.get("TargetPrice", ""))
        entry_elem.set("CurrentPrice", row.get("CurrentPrice", ""))
        entry_elem.set("PERatio", row.get("PERatio", ""))
        entry_elem.set("ROIC", row.get("ROIC", ""))

    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    return xml_path


def fetch_stock_metrics(ticker: str) -> Dict[str, Any]:
    ticker = (ticker or "").strip()
    if not ticker:
        return {"ticker": ticker, "current_price": "N/A", "pe_ratio": "N/A", "roic": "N/A", "error": "Empty ticker"}

    try:
        stock = yf.Ticker(ticker)
        info = getattr(stock, "info", {}) or {}
        current_price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
        pe_ratio = info.get("trailingPE", "N/A")
        roic = info.get("returnOnEquity", "N/A")
        if isinstance(roic, (int, float)):
            roic = f"{roic * 100:.2f}%"
        return {
            "ticker": ticker,
            "current_price": current_price,
            "pe_ratio": pe_ratio,
            "roic": roic,
            "error": None,
        }
    except Exception as exc:
        return {"ticker": ticker, "current_price": "N/A", "pe_ratio": "N/A", "roic": "N/A", "error": str(exc)}


def update_rows_from_yahoo(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    updated_rows: List[Dict[str, Any]] = []
    for row in rows:
        ticker = str(row.get("TickerName", "")).strip()
        if not ticker:
            updated_rows.append(row)
            continue

        metrics = fetch_stock_metrics(ticker)
        updated_row = dict(row)
        updated_row["CurrentPrice"] = format_value(metrics.get("current_price"))
        updated_row["PERatio"] = format_value(metrics.get("pe_ratio"))
        updated_row["ROIC"] = format_value(metrics.get("roic"))
        if metrics.get("error"):
            updated_row["CurrentPrice"] = f"Error: {metrics['error']}"
        updated_rows.append(updated_row)

    return updated_rows


def format_value(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    if value is None:
        return "N/A"
    return str(value)


def build_report(rows: List[Dict[str, Any]]) -> str:
    lines = ["Price Target Report", "===================", ""]
    for index, row in enumerate(rows, start=1):
        ticker = row.get("TickerName", "")
        target = row.get("TargetPrice", "")
        current = row.get("CurrentPrice", "")
        pe = row.get("PERatio", "")
        roic = row.get("ROIC", "")
        lines.append(f"{index}. {ticker or '(empty)'} | Target={target} | Current={current} | P/E={pe} | ROIC={roic}")
    return "\n".join(lines)


def send_email_report(subject: str, body: str, recipient: Optional[str] = None) -> None:
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("Email skipped: this run is not being executed from GitHub Actions.")
        return

    host = os.getenv("SMTP_HOST", "").strip()
    port = os.getenv("SMTP_PORT", "587").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    to_email = (recipient or os.getenv("EMAIL_TO", "")).strip()
    from_email = os.getenv("FROM_EMAIL", username or "github-actions@localhost")

    if not host or not username or not password or not to_email:
        print("Email not sent: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, or EMAIL_TO is missing.")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(host, int(port)) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)

    print(f"Email sent to {to_email}")
