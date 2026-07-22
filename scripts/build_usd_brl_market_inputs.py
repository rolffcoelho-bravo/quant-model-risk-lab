"""Build a governed USD/BRL market-input snapshot from official sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

import sys

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qmrl.fx_market_inputs import (
    FXMarketInputSnapshot,
    validate_market_input_snapshot,
)


USD_CURVE_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "usd_treasury_curve_nodes.csv"
)

RAW_SPOT_PATH = (
    ROOT
    / "data"
    / "official"
    / "raw"
    / "bcb_usd_brl_sgs1.json"
)

RAW_SELIC_PATH = (
    ROOT
    / "data"
    / "official"
    / "raw"
    / "bcb_selic_target_sgs432.json"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "usd_brl_market_inputs.csv"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "official"
    / "processed"
    / "usd_brl_market_input_manifest.json"
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_bcb_number(value: object) -> float:
    text = str(value).strip().replace(",", ".")
    return float(text)


def bcb_url(
    series_code: int,
    start_date: date,
    end_date: date,
) -> str:
    query = urlencode(
        {
            "formato": "json",
            "dataInicial": start_date.strftime("%d/%m/%Y"),
            "dataFinal": end_date.strftime("%d/%m/%Y"),
        }
    )

    return (
        "https://api.bcb.gov.br/dados/serie/"
        f"bcdata.sgs.{series_code}/dados?{query}"
    )


def download_json(
    *,
    url: str,
    destination: Path,
    refresh: bool,
) -> bytes:
    if destination.exists() and not refresh:
        return destination.read_bytes()

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    last_error: Exception | None = None

    for attempt in range(3):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": (
                        "quant-model-risk-lab/"
                        "fx-input-validation"
                    )
                },
            )

            with urlopen(
                request,
                timeout=45,
            ) as response:
                content = response.read()

            json.loads(content.decode("utf-8"))
            destination.write_bytes(content)
            return content
        except Exception as exc:
            last_error = exc

            if attempt < 2:
                time.sleep(2 ** attempt)

    if destination.exists():
        return destination.read_bytes()

    raise RuntimeError(
        f"Could not retrieve official BCB data from {url}"
    ) from last_error


def parse_bcb_series(
    content: bytes,
) -> pd.DataFrame:
    payload = json.loads(content.decode("utf-8"))

    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "The BCB response contains no observations."
        )

    frame = pd.DataFrame(payload)

    if not {"data", "valor"}.issubset(frame.columns):
        raise ValueError(
            "The BCB response does not contain data and valor."
        )

    frame["date"] = pd.to_datetime(
        frame["data"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    frame["value"] = frame["valor"].map(
        parse_bcb_number
    )

    frame = frame.dropna(
        subset=["date", "value"]
    ).sort_values("date")

    if frame.empty:
        raise ValueError(
            "No valid BCB observations were parsed."
        )

    return frame[["date", "value"]]


def latest_on_or_before(
    frame: pd.DataFrame,
    as_of_date: date,
) -> tuple[date, float]:
    cutoff = pd.Timestamp(as_of_date)

    eligible = frame[
        frame["date"] <= cutoff
    ]

    if eligible.empty:
        raise ValueError(
            "No source observation exists on or before the as-of date."
        )

    row = eligible.iloc[-1]

    return (
        row["date"].date(),
        float(row["value"]),
    )


def read_usd_one_year_rate() -> tuple[date, float]:
    if not USD_CURVE_PATH.exists():
        raise FileNotFoundError(
            "USD Treasury curve nodes are missing."
        )

    curve = pd.read_csv(USD_CURVE_PATH)

    if not {"date", "DGS1"}.issubset(curve.columns):
        raise ValueError(
            "USD curve must contain date and DGS1."
        )

    curve["date"] = pd.to_datetime(
        curve["date"],
        errors="coerce",
    )

    curve["DGS1"] = pd.to_numeric(
        curve["DGS1"],
        errors="coerce",
    )

    curve = curve.dropna(
        subset=["date", "DGS1"]
    ).sort_values("date")

    if curve.empty:
        raise ValueError(
            "USD curve contains no valid one-year observation."
        )

    row = curve.iloc[-1]

    return (
        row["date"].date(),
        float(row["DGS1"]) / 100.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh cached BCB source responses.",
    )
    args = parser.parse_args()

    foreign_date, foreign_rate = (
        read_usd_one_year_rate()
    )

    as_of_date = foreign_date
    start_date = as_of_date - timedelta(days=370)

    spot_url = bcb_url(
        1,
        start_date,
        as_of_date,
    )

    selic_url = bcb_url(
        432,
        start_date,
        as_of_date,
    )

    spot_bytes = download_json(
        url=spot_url,
        destination=RAW_SPOT_PATH,
        refresh=args.refresh,
    )

    selic_bytes = download_json(
        url=selic_url,
        destination=RAW_SELIC_PATH,
        refresh=args.refresh,
    )

    spot_frame = parse_bcb_series(spot_bytes)
    selic_frame = parse_bcb_series(selic_bytes)

    spot_date, spot_rate = latest_on_or_before(
        spot_frame,
        as_of_date,
    )

    domestic_date, domestic_rate_percent = (
        latest_on_or_before(
            selic_frame,
            as_of_date,
        )
    )

    domestic_rate = domestic_rate_percent / 100.0

    snapshot = FXMarketInputSnapshot(
        as_of_date=as_of_date,
        currency_pair="USD/BRL",
        quote_convention="BRL per USD",
        spot_rate_brl_per_usd=spot_rate,
        domestic_rate_brl=domestic_rate,
        foreign_rate_usd=foreign_rate,
        spot_source_id="BCB_SGS_1",
        domestic_rate_source_id="BCB_SGS_432",
        foreign_rate_source_id="FRED_DGS1",
        spot_observation_date=spot_date,
        domestic_rate_observation_date=domestic_date,
        foreign_rate_observation_date=foreign_date,
        input_contract_status="PASS",
    )

    validate_market_input_snapshot(snapshot)

    output = pd.DataFrame(
        [
            {
                "as_of_date": snapshot.as_of_date.isoformat(),
                "currency_pair": snapshot.currency_pair,
                "quote_convention": (
                    snapshot.quote_convention
                ),
                "spot_rate_brl_per_usd": (
                    snapshot.spot_rate_brl_per_usd
                ),
                "domestic_rate_brl": (
                    snapshot.domestic_rate_brl
                ),
                "foreign_rate_usd": (
                    snapshot.foreign_rate_usd
                ),
                "spot_source_id": (
                    snapshot.spot_source_id
                ),
                "domestic_rate_source_id": (
                    snapshot.domestic_rate_source_id
                ),
                "foreign_rate_source_id": (
                    snapshot.foreign_rate_source_id
                ),
                "spot_observation_date": (
                    snapshot.spot_observation_date.isoformat()
                ),
                "domestic_rate_observation_date": (
                    snapshot.domestic_rate_observation_date.isoformat()
                ),
                "foreign_rate_observation_date": (
                    snapshot.foreign_rate_observation_date.isoformat()
                ),
                "input_contract_status": (
                    snapshot.input_contract_status
                ),
            }
        ]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    manifest: dict[str, Any] = {
        "manifest_id": "QMRL-FX-INPUT-001",
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "as_of_date": as_of_date.isoformat(),
        "currency_pair": "USD/BRL",
        "quote_convention": "BRL per USD",
        "input_contract_status": "PASS",
        "sources": [
            {
                "source_id": "BCB_SGS_1",
                "description": (
                    "Daily USD sell exchange rate, BRL per USD"
                ),
                "url": spot_url,
                "raw_path": RAW_SPOT_PATH.relative_to(
                    ROOT
                ).as_posix(),
                "raw_sha256": sha256_bytes(
                    spot_bytes
                ),
                "observation_date": spot_date.isoformat(),
                "unit": "BRL per USD",
            },
            {
                "source_id": "BCB_SGS_432",
                "description": (
                    "Copom Selic target proxy"
                ),
                "url": selic_url,
                "raw_path": RAW_SELIC_PATH.relative_to(
                    ROOT
                ).as_posix(),
                "raw_sha256": sha256_bytes(
                    selic_bytes
                ),
                "observation_date": (
                    domestic_date.isoformat()
                ),
                "source_unit": "percent per year",
                "model_unit": "annual decimal",
            },
            {
                "source_id": "FRED_DGS1",
                "description": (
                    "One-year USD Treasury yield proxy"
                ),
                "path": USD_CURVE_PATH.relative_to(
                    ROOT
                ).as_posix(),
                "file_sha256": sha256_file(
                    USD_CURVE_PATH
                ),
                "observation_date": (
                    foreign_date.isoformat()
                ),
                "source_unit": "percent per year",
                "model_unit": "annual decimal",
            },
        ],
        "output_path": OUTPUT_PATH.relative_to(
            ROOT
        ).as_posix(),
        "output_sha256": sha256_file(
            OUTPUT_PATH
        ),
        "model_boundaries": [
            (
                "Selic target is a transparent domestic-rate "
                "proxy rather than a tradable BRL zero curve."
            ),
            (
                "DGS1 is a transparent USD foreign-rate proxy "
                "rather than a collateral-specific discount curve."
            ),
            (
                "Market option quotes are not included in this "
                "input snapshot."
            ),
        ],
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(
        f"Wrote {OUTPUT_PATH.relative_to(ROOT)}"
    )
    print(
        f"Wrote {MANIFEST_PATH.relative_to(ROOT)}"
    )
    print(
        f"As-of date: {as_of_date.isoformat()}"
    )
    print(
        f"USD/BRL spot: {spot_rate:.6f}"
    )
    print(
        f"BRL rate proxy: {domestic_rate:.6f}"
    )
    print(
        f"USD rate proxy: {foreign_rate:.6f}"
    )
    print("Input contract: PASS")


if __name__ == "__main__":
    main()