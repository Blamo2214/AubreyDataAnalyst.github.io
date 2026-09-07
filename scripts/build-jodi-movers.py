from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

JODI_DIR = Path('data/jodi')
COUNTRY_DIR = JODI_DIR / 'countries'
SUMMARY_PATH = JODI_DIR / 'summary.json'
OUTPUT_PATH = JODI_DIR / 'movers.json'

MAX_STALENESS_MONTHS = 6
FLOW_MIN_PRIOR_VALUE = 0.05  # million barrels per day = 50 kb/d
STOCK_MIN_PRIOR_VALUE = 1.0  # million barrels

SERIES_CONFIG = {
    'crude_production': {
        'name': 'Crude Production',
        'rank_by': 'percent',
        'min_prior': FLOW_MIN_PRIOR_VALUE,
    },
    'crude_imports': {
        'name': 'Crude Imports',
        'rank_by': 'percent',
        'min_prior': FLOW_MIN_PRIOR_VALUE,
    },
    'crude_exports': {
        'name': 'Crude Exports',
        'rank_by': 'percent',
        'min_prior': FLOW_MIN_PRIOR_VALUE,
    },
    'refinery_intake': {
        'name': 'Refinery Intake',
        'rank_by': 'percent',
        'min_prior': FLOW_MIN_PRIOR_VALUE,
    },
    'closing_stocks': {
        'name': 'Closing Crude Stocks',
        'rank_by': 'absolute',
        'min_prior': STOCK_MIN_PRIOR_VALUE,
    },
}


def month_distance(older: str, newer: str) -> int:
    older_year, older_month = map(int, older.split('-'))
    newer_year, newer_month = map(int, newer.split('-'))
    return (newer_year - older_year) * 12 + (newer_month - older_month)


def previous_year_month(month: str) -> str:
    year, month_number = map(int, month.split('-'))
    return f'{year - 1:04d}-{month_number:02d}'


def load_json(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def main() -> None:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f'Missing {SUMMARY_PATH}')

    if not COUNTRY_DIR.exists():
        raise FileNotFoundError(f'Missing {COUNTRY_DIR}')

    summary = load_json(SUMMARY_PATH)
    global_latest = summary.get('latest_global_reported_month')

    if not global_latest:
        raise RuntimeError('summary.json does not contain latest_global_reported_month')

    result = {
        'source': 'JODI Oil World Database',
        'dataset': 'Extended Primary',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'latest_global_reported_month': global_latest,
        'methodology': {
            'max_staleness_months': MAX_STALENESS_MONTHS,
            'flow_min_prior_value_mbd': FLOW_MIN_PRIOR_VALUE,
            'stock_min_prior_value_million_barrels': STOCK_MIN_PRIOR_VALUE,
            'comparison': (
                'Latest available observation versus the exact same month one year earlier. '
                'Flow series are ranked by percentage change; closing stocks are ranked '
                'by absolute million-barrel change.'
            ),
        },
        'series': {},
    }

    country_files = sorted(COUNTRY_DIR.glob('*.json'))

    for series_key, config in SERIES_CONFIG.items():
        eligible = []
        unit = None

        for country_path in country_files:
            country_data = load_json(country_path)
            country = country_data.get('country', {})
            series = country_data.get('series', {}).get(series_key)

            if not series:
                continue

            observations = series.get('observations') or []
            if not observations:
                continue

            latest = observations[-1]
            latest_month = latest.get('date')
            latest_value = latest.get('value')

            if not latest_month or not isinstance(latest_value, (int, float)):
                continue

            stale_months = month_distance(latest_month, global_latest)

            if stale_months < 0 or stale_months > MAX_STALENESS_MONTHS:
                continue

            year_ago_month = previous_year_month(latest_month)
            year_ago = next(
                (item for item in observations if item.get('date') == year_ago_month),
                None,
            )

            if not year_ago:
                continue

            year_ago_value = year_ago.get('value')

            if not isinstance(year_ago_value, (int, float)):
                continue

            if year_ago_value < config['min_prior']:
                continue

            absolute_change = latest_value - year_ago_value
            percent_change = (absolute_change / year_ago_value) * 100
            unit = series.get('unit') or unit

            eligible.append({
                'code': country.get('code') or country_path.stem,
                'name': country.get('name') or country_path.stem,
                'latest_month': latest_month,
                'latest_value': round(latest_value, 6),
                'year_ago_month': year_ago_month,
                'year_ago_value': round(year_ago_value, 6),
                'absolute_change': round(absolute_change, 6),
                'percent_change': round(percent_change, 3),
                'stale_months': stale_months,
            })

        if config['rank_by'] == 'absolute':
            gainers = sorted(
                (item for item in eligible if item['absolute_change'] > 0),
                key=lambda item: item['absolute_change'],
                reverse=True,
            )[:3]
            losers = sorted(
                (item for item in eligible if item['absolute_change'] < 0),
                key=lambda item: item['absolute_change'],
            )[:3]
        else:
            gainers = sorted(
                (item for item in eligible if item['percent_change'] > 0),
                key=lambda item: item['percent_change'],
                reverse=True,
            )[:3]
            losers = sorted(
                (item for item in eligible if item['percent_change'] < 0),
                key=lambda item: item['percent_change'],
            )[:3]

        result['series'][series_key] = {
            'name': config['name'],
            'unit': unit,
            'rank_by': config['rank_by'],
            'eligible_country_count': len(eligible),
            'gainers': gainers,
            'losers': losers,
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')

    print(f'Wrote {OUTPUT_PATH}')
    for key, series in result['series'].items():
        print(
            f"{key}: {series['eligible_country_count']} eligible, "
            f"{len(series['gainers'])} gainers, {len(series['losers'])} losers"
        )


if __name__ == '__main__':
    main()
