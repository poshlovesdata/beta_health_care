from typing import Optional, List

import os
from sqlalchemy import create_engine, text

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, future=True)

app = FastAPI(title="BetaHealthCare API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "BetaHealthCare API",
        "version": "0.2.0",
        "endpoints": [
            "/facilities",
            "/facilities/{facility_id}",
            "/lga-signals",
        ],
    }


@app.get("/facilities")
def list_facilities(
    state: Optional[str] = None,
    lga: Optional[str] = None,
    facility_type: Optional[str] = Query(None, description="hospital | health_center | health_post"),
    ownership: Optional[str] = Query(None, description="public | private | ngo"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    base = "SELECT * FROM facilities_master"
    where = []
    params: List = []
    if state:
        where.append("state = :state")
        params.append(("state", state))
    if lga:
        where.append("lga = :lga")
        params.append(("lga", lga))
    if facility_type:
        where.append("facility_type = :facility_type")
        params.append(("facility_type", facility_type))
    if ownership:
        where.append("ownership = :ownership")
        params.append(("ownership", ownership))

    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY facility_id LIMIT :limit OFFSET :offset"

    bind = {k: v for k, v in params}
    bind.update({"limit": limit, "offset": offset})

    with engine.connect() as conn:
        rows = conn.execute(text(base), bind).fetchall()
        return [dict(r._mapping) for r in rows]


@app.get("/facilities/{facility_id}")
def get_facility(facility_id: str):
    with engine.connect() as conn:
        fac = conn.execute(
            text("SELECT * FROM facilities_master WHERE facility_id = :fid"),
            {"fid": facility_id},
        ).fetchone()
        if not fac:
            raise HTTPException(status_code=404, detail="Facility not found")

        infra = conn.execute(
            text(
                "SELECT has_improved_water, has_improved_toilet, has_electricity, power_source, infrastructure_index "
                "FROM facility_infrastructure WHERE facility_id = :fid"
            ),
            {"fid": facility_id},
        ).fetchone()

        services = conn.execute(
            text("SELECT service_code, service_name, active FROM facility_services WHERE facility_id = :fid"),
            {"fid": facility_id},
        ).fetchall()

        latest_status = conn.execute(
            text(
                "SELECT * FROM facility_live_status WHERE facility_id = :fid ORDER BY status_timestamp DESC LIMIT 1"
            ),
            {"fid": facility_id},
        ).fetchone()

        return {
            "facility": dict(fac._mapping),
            "infrastructure": dict(infra._mapping) if infra else None,
            "services": [dict(s._mapping) for s in services],
            "latest_status": dict(latest_status._mapping) if latest_status else None,
        }


@app.get("/lga-signals")
def lga_signals(
    state: Optional[str] = None,
    lga: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    base = "SELECT * FROM lga_daily_signals"
    where = []
    params: List = []
    if state:
        where.append("state = :state")
        params.append(("state", state))
    if lga:
        where.append("lga = :lga")
        params.append(("lga", lga))
    if date_from:
        where.append("date >= :date_from")
        params.append(("date_from", date_from))
    if date_to:
        where.append("date <= :date_to")
        params.append(("date_to", date_to))

    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY date DESC LIMIT :limit OFFSET :offset"

    bind = {k: v for k, v in params}
    bind.update({"limit": limit, "offset": offset})

    with engine.connect() as conn:
        rows = conn.execute(text(base), bind).fetchall()
        return [dict(r._mapping) for r in rows]