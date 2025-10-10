import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
print(OUTPUT_DIR)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TABLES = {
    "facilities_master": "facilities_master.csv",
    "facility_infrastructure": "facility_infrastructure.csv",
    "facility_equipment": "facility_equipment.csv",
    "medicine_catalog": "medicine_catalog.csv",
    "facility_medicine_stock": "facility_medicine_stock.csv",
    "facility_hours": "facility_hours.csv",
    "facility_services": "facility_services.csv",
    "facility_live_status": "facility_live_status.csv",
    "facility_daily_metrics": "facility_daily_metrics.csv",
    "facility_referrals": "facility_referrals.csv",
    "lga_daily_signals": "lga_daily_signals.csv",
}


def load_csv_to_pg(csv_path: Path, table_name: str, engine):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df.to_sql(table_name, engine, if_exists="replace", index=False)


def create_indexes(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facilities_id ON facilities_master(facility_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_infra_facility_id ON facility_infrastructure(facility_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_services_facility_id ON facility_services(facility_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_daily_facility_date ON facility_daily_metrics(facility_id, date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_referrals_from_date ON facility_referrals(from_facility_id, date_time)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lga_signals_date_lga ON lga_daily_signals(date, state, lga)"))


def main():
    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Output directory not found: {OUTPUT_DIR}")

    engine = create_engine(DATABASE_URL, future=True)

    for table_name, filename in TABLES.items():
        csv_path = OUTPUT_DIR / filename
        if not csv_path.exists():
            print(f"Skipping missing file: {csv_path}")
            continue
        print(f"Loading {filename} into table '{table_name}'...")
        load_csv_to_pg(csv_path, table_name, engine)

    create_indexes(engine)
    print("Postgres load complete.")


if __name__ == "__main__":
    main()