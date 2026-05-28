import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_current_trains():
    url = "https://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_current_trains(xml_text):
    root = ET.fromstring(xml_text)

    rows = []

    for train in root:
        row = {}
        for child in train:
            tag = child.tag.split("}")[-1]
            row[tag] = child.text
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    print("Fetching Irish Rail current train data")

    xml_text = fetch_current_trains()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_file = RAW_DIR / f"irish_rail_current_trains_{timestamp}.xml"
    csv_file = RAW_DIR / f"irish_rail_current_trains_{timestamp}.csv"

    raw_file.write_text(xml_text, encoding="utf-8")

    df = parse_current_trains(xml_text)
    df.to_csv(csv_file, index=False)

    print(f"Rows collected: {len(df)}")
    print(f"Raw XML saved to: {raw_file}")
    print(f"CSV saved to: {csv_file}")

    if not df.empty:
        print(df.head())


if __name__ == "__main__":
    main()