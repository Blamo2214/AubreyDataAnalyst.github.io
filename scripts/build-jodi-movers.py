import json
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parents[1]

JODI_DIR = BASE_DIR / "data" / "jodi"
COUNTRIES_DIR = JODI_DIR / "countries"
SUMMARY_FILE = JODI_DIR / "summary.json"
OUTPUT_FILE = JODI_DIR / "movers.json"


TOP_PRODUCER_COUNT = 20
MAX_STALE_MONTHS = 6


FLOW_CONFIG = {
    "crude_production": {
        "name": "Crude Oil Production",
        "unit": "million barrels per day",
        "rank_by": "percent"
    },

    "crude_imports": {
        "name": "Crude Oil Imports",
        "unit": "million barrels per day",
        "rank_by": "percent"
    },

    "crude_exports": {
        "name": "Crude Oil Exports",
        "unit": "million barrels per day",
        "rank_by": "percent"
    },

    "refinery_intake": {
        "name": "Refinery Crude Intake",
        "unit": "million barrels per day",
        "rank_by": "percent"
    },

    "closing_stocks": {
        "name": "Closing Crude Oil Stocks",
        "unit": "million barrels",
        "rank_by": "absolute"
    }
}


def month_number(month_string):
    year, month = map(int, month_string.split("-"))
    return year * 12 + month


def months_between(older, newer):
    return month_number(newer) - month_number(older)


def prior_year_month(month_string):
    year, month = map(int, month_string.split("-"))
    return f"{year - 1:04d}-{month:02d}"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# LOAD JODI SUMMARY
# ---------------------------------------------------------

summary = load_json(SUMMARY_FILE)

global_latest_month = summary["latest_global_reported_month"]


# ---------------------------------------------------------
# LOAD COUNTRY FILES
# ---------------------------------------------------------

countries = {}

for country_entry in summary["countries"]:

    country_code = country_entry["code"]

    country_file = JODI_DIR / country_entry["file"]

    if not country_file.exists():
        print(f"Skipping missing country file: {country_file}")
        continue

    country_data = load_json(country_file)

    countries[country_code] = country_data


print(f"Loaded {len(countries)} JODI country files.")


# ---------------------------------------------------------
# IDENTIFY TOP 20 CURRENT CRUDE PRODUCERS
# ---------------------------------------------------------

producer_candidates = []

for country_code, country_data in countries.items():

    production = country_data.get(
        "series",
        {}
    ).get(
        "crude_production"
    )

    if not production:
        continue

    observations = production.get(
        "observations",
        []
    )

    if not observations:
        continue

    latest = observations[-1]

    latest_month = latest["date"]

    # Exclude materially stale production reporters.
    stale_months = months_between(
        latest_month,
        global_latest_month
    )

    if stale_months > MAX_STALE_MONTHS:
        continue

    latest_value = float(
        latest["value"]
    )

    producer_candidates.append({
        "code": country_code,
        "name": country_data["country"]["name"],
        "production": latest_value,
        "latest_month": latest_month
    })


producer_candidates.sort(
    key=lambda item: item["production"],
    reverse=True
)


top_producers = producer_candidates[
    :TOP_PRODUCER_COUNT
]


top_producer_codes = {
    item["code"]
    for item in top_producers
}


print()
print("Top 20 JODI crude producers:")

for rank, producer in enumerate(
    top_producers,
    start=1
):
    print(
        f"{rank:>2}. "
        f"{producer['name']:<30} "
        f"{producer['production']:.3f} M b/d "
        f"({producer['latest_month']})"
    )


# ---------------------------------------------------------
# CALCULATE YOY MOVERS
# ---------------------------------------------------------

movers_output = {}


for series_key, config in FLOW_CONFIG.items():

    candidates = []

    for country_code in top_producer_codes:

        country_data = countries.get(
            country_code
        )

        if not country_data:
            continue

        series = country_data.get(
            "series",
            {}
        ).get(
            series_key
        )

        if not series:
            continue

        observations = series.get(
            "observations",
            []
        )

        if not observations:
            continue

        latest = observations[-1]

        latest_month = latest["date"]
        latest_value = float(latest["value"])


        # ---------------------------------------------
        # EXCLUDE STALE SERIES
        # ---------------------------------------------

        stale_months = months_between(
            latest_month,
            global_latest_month
        )

        if stale_months > MAX_STALE_MONTHS:
            continue


        # ---------------------------------------------
        # FIND EXACT SAME MONTH ONE YEAR EARLIER
        # ---------------------------------------------

        target_month = prior_year_month(
            latest_month
        )

        year_ago = next(
            (
                item
                for item in observations
                if item["date"] == target_month
            ),
            None
        )

        if year_ago is None:
            continue


        year_ago_value = float(
            year_ago["value"]
        )


        # ---------------------------------------------
        # FILTER NEAR-ZERO BASES
        # ---------------------------------------------

        if series_key == "closing_stocks":

            minimum_base = 1.0

        else:

            minimum_base = 0.05


        if abs(year_ago_value) < minimum_base:
            continue


        # ---------------------------------------------
        # CALCULATE CHANGE
        # ---------------------------------------------

        absolute_change = (
            latest_value -
            year_ago_value
        )

        percent_change = (
            absolute_change /
            abs(year_ago_value)
        ) * 100


        candidates.append({
            "code": country_code,
            "name": country_data["country"]["name"],
            "latest_month": latest_month,
            "year_ago_month": target_month,
            "latest_value": round(
                latest_value,
                4
            ),
            "year_ago_value": round(
                year_ago_value,
                4
            ),
            "absolute_change": round(
                absolute_change,
                4
            ),
            "percent_change": round(
                percent_change,
                2
            )
        })


    # -------------------------------------------------
    # RANK SERIES
    # -------------------------------------------------

    if config["rank_by"] == "absolute":

        gainers = sorted(
            candidates,
            key=lambda item: item[
                "absolute_change"
            ],
            reverse=True
        )

        losers = sorted(
            candidates,
            key=lambda item: item[
                "absolute_change"
            ]
        )

    else:

        gainers = sorted(
            candidates,
            key=lambda item: item[
                "percent_change"
            ],
            reverse=True
        )

        losers = sorted(
            candidates,
            key=lambda item: item[
                "percent_change"
            ]
        )


    # Only positive changes belong in gainers.
    gainers = [
        item
        for item in gainers
        if item["absolute_change"] > 0
    ][:3]


    # Only negative changes belong in losers.
    losers = [
        item
        for item in losers
        if item["absolute_change"] < 0
    ][:3]


    movers_output[series_key] = {
        "name": config["name"],
        "unit": config["unit"],
        "rank_by": config["rank_by"],
        "eligible_country_count": len(
            candidates
        ),
        "gainers": gainers,
        "losers": losers
    }


# ---------------------------------------------------------
# BUILD OUTPUT
# ---------------------------------------------------------

output = {
    "source": "JODI Oil World Database",
    "generated_at": datetime.now(
        timezone.utc
    ).isoformat(),
    "latest_global_reported_month":
        global_latest_month,

    "scope": {
        "description":
            "Top 20 crude-producing countries "
            "in current JODI data",
        "producer_count":
            TOP_PRODUCER_COUNT,
        "maximum_staleness_months":
            MAX_STALE_MONTHS,
        "countries":
            top_producers
    },

    "series":
        movers_output
}


# ---------------------------------------------------------
# WRITE JSON
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=2,
        ensure_ascii=False
    )


print()
print(
    f"Created {OUTPUT_FILE}"
)

print(
    "Global YoY Movers now restricted "
    "to the top 20 current JODI crude producers."
)
