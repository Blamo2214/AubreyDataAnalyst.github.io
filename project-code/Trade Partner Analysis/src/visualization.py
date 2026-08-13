import html
import json
import re
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from src.config import (
    DEFAULT_AXIS_PADDING,
    DEFAULT_FIGURE_HEIGHT,
    DEFAULT_FIGURE_WIDTH,
    DEFAULT_FRAME_DURATION,
    DEFAULT_TRANSITION_DURATION,
    MARKER_OUTLINE_COLOR,
    NEUTRAL_COLOR,
    OUTPUT_DIR,
    X_PARTNER_COLOR,
    Y_PARTNER_COLOR,
)


CONTINENT_ORDER = [
    "Europe",
    "Asia",
    "North America",
    "South America",
    "Africa",
    "Oceania",
    "Other",
]


def _safe_slug(value: object) -> str:
    """Return a filesystem-safe slug."""

    slug = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower())
    return slug.strip("-") or "visualization"


def _get_text(
    metric_config: dict[str, object],
    key: str,
    fallback: str,
) -> str:
    """Return a clean metadata value or a fallback."""

    value = metric_config.get(key, "")

    if pd.isna(value):
        return fallback

    text = str(value).strip()
    return text or fallback


def _get_trade_color(
    x_value: float | None,
    y_value: float | None,
) -> str:
    """Color points by whichever configured partner has the larger value."""

    if x_value is None or y_value is None:
        return NEUTRAL_COLOR

    if y_value > x_value:
        return Y_PARTNER_COLOR

    if x_value > y_value:
        return X_PARTNER_COLOR

    return NEUTRAL_COLOR


def _build_chart_labels(
    metric_config: dict[str, object],
) -> dict[str, str]:
    """Build titles and labels from metric metadata."""

    metric_name = _get_text(
        metric_config,
        "Metric",
        "Trade Metric",
    )

    display_name = _get_text(
        metric_config,
        "Display Name",
        metric_name,
    )

    x_partner = _get_text(
        metric_config,
        "Default X Partner",
        "X Partner",
    )

    y_partner = _get_text(
        metric_config,
        "Default Y Partner",
        "Y Partner",
    )

    suffix = _get_text(
        metric_config,
        "Axis Suffix",
        "",
    )

    title = f"{display_name}: {x_partner} vs. {y_partner}"

    if suffix == "%":
        x_title = f"{x_partner} ({suffix})"
        y_title = f"{y_partner} ({suffix})"
    elif suffix:
        x_title = f"{x_partner} ({suffix})"
        y_title = f"{y_partner} ({suffix})"
    else:
        x_title = x_partner
        y_title = y_partner

    return {
        "metric_name": metric_name,
        "display_name": display_name,
        "description": _get_text(
            metric_config,
            "Description",
            "",
        ),
        "x_partner": x_partner,
        "y_partner": y_partner,
        "suffix": suffix,
        "title": title,
        "x_title": x_title,
        "y_title": y_title,
        "output_slug": _safe_slug(
            _get_text(
                metric_config,
                "Output Slug",
                metric_name,
            )
        ),
    }


def create_trade_animation(
    metric_data: pd.DataFrame,
    metric_config: dict[str, object],
) -> go.Figure:
    """
    Create one reusable animated scatter plot for a selected metric.

    Required metric_data columns:
        Year, Country, Continent, X Value, Y Value
    """

    required_columns = {
        "Year",
        "Country",
        "Continent",
        "X Value",
        "Y Value",
    }

    missing_columns = required_columns.difference(metric_data.columns)

    if missing_columns:
        raise KeyError(
            "Chart data is missing these required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if metric_data.empty:
        raise ValueError("No rows are available for this metric.")

    labels = _build_chart_labels(metric_config)

    countries = sorted(metric_data["Country"].dropna().unique())
    years = sorted(metric_data["Year"].dropna().unique())
    first_year = years[0]

    x_max = float(metric_data["X Value"].max()) * DEFAULT_AXIS_PADDING
    y_max = float(metric_data["Y Value"].max()) * DEFAULT_AXIS_PADDING

    fig = go.Figure()

    initial_data = metric_data[
        metric_data["Year"] == first_year
    ]

    for country in countries:
        country_row = initial_data[
            initial_data["Country"] == country
        ]

        if country_row.empty:
            x_value = None
            y_value = None
            continent = "Other"
        else:
            x_value = float(country_row["X Value"].iloc[0])
            y_value = float(country_row["Y Value"].iloc[0])
            continent = str(country_row["Continent"].iloc[0])

        marker_color = _get_trade_color(x_value, y_value)
        difference = None

        if x_value is not None and y_value is not None:
            difference = round(y_value - x_value, 2)
        fig.add_trace(
            go.Scatter(
                x=[x_value],
                y=[y_value],
                mode="markers+text",
                name=country,
                meta={"continent": continent},
                text=[country],
                textposition="top center",
                textfont={"size": 10},
                marker={
                    "size": 14,
                    "color": marker_color,
                    "opacity": 0.85,
                    "line": {
                        "width": 1,
                        "color": MARKER_OUTLINE_COLOR,
                    },
                },
                customdata=[[first_year, continent, difference]],
                hovertemplate=(
                    "<b>%{fullData.name}</b><br><br>"
                    "Continent: %{customdata[1]}<br>"
                    "Year: %{customdata[0]}<br><br>"
                    f"{html.escape(labels['x_partner'])}: "
                    "%{x:.2f}"
                    f"{html.escape(labels['suffix'])}<br>"
                    f"{html.escape(labels['y_partner'])}: "
                    "%{y:.2f}"
                    f"{html.escape(labels['suffix'])}<br><br>"
                    "U.S. minus China: "
                    "%{customdata[2]:+.2f}"
                    f"{html.escape(labels['suffix'])}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    frames: list[go.Frame] = []

    for year in years:
        year_data = metric_data[
            metric_data["Year"] == year
        ]

        frame_traces: list[go.Scatter] = []

        for country in countries:
            country_row = year_data[
                year_data["Country"] == country
            ]

            if country_row.empty:
                x_value = None
                y_value = None
                continent = "Other"
            else:
                x_value = float(country_row["X Value"].iloc[0])
                y_value = float(country_row["Y Value"].iloc[0])
                continent = str(country_row["Continent"].iloc[0])

            marker_color = _get_trade_color(x_value, y_value)
            difference = None

            if x_value is not None and y_value is not None:
                difference = round(y_value - x_value, 2)

            frame_traces.append(
                go.Scatter(
                    x=[x_value],
                    y=[y_value],
                    text=[country],
                    customdata=[[year, continent, difference]],
                    marker={"color": marker_color},
                )
            )

        frames.append(
            go.Frame(
                data=frame_traces,
                name=str(year),
                traces=list(range(len(countries))),
            )
        )

    fig.frames = frames

    slider_steps = [
        {
            "label": str(year),
            "method": "animate",
            "args": [
                [str(year)],
                {
                    "mode": "immediate",
                    "frame": {
                        "duration": DEFAULT_FRAME_DURATION,
                        "redraw": False,
                    },
                    "transition": {
                        "duration": DEFAULT_TRANSITION_DURATION,
                    },
                },
            ],
        }
        for year in years
    ]

    fig.update_layout(
        template="plotly_dark",
        width=DEFAULT_FIGURE_WIDTH,
        height=DEFAULT_FIGURE_HEIGHT,
        title={
            "text": labels["title"],
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24},
        },
        xaxis={
            "title": labels["x_title"],
            "range": [0, x_max],
            "ticksuffix": labels["suffix"],
            "showgrid": True,
            "zeroline": True,
        },
        yaxis={
            "title": labels["y_title"],
            "range": [0, y_max],
            "ticksuffix": labels["suffix"],
            "showgrid": True,
            "zeroline": True,
        },
        shapes=[
    {
        "type": "line",
        "x0": 0,
        "y0": 0,
        "x1": min(x_max, y_max),
        "y1": min(x_max, y_max),
        "line": {
            "color": "#888888",
            "width": 1.5,
            "dash": "dash",
        },
        "layer": "below",
    }
    ],
        margin={
            "l": 90,
            "r": 40,
            "t": 90,
            "b": 120,
        },
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.1,
                "y": -0.12,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "fromcurrent": True,
                                "mode": "immediate",
                                "frame": {
                                    "duration": DEFAULT_FRAME_DURATION,
                                    "redraw": False,
                                },
                                "transition": {
                                    "duration": DEFAULT_TRANSITION_DURATION,
                                },
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "mode": "immediate",
                                "frame": {
                                    "duration": 0,
                                    "redraw": False,
                                },
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Year: "},
                "pad": {"t": 40},
                "steps": slider_steps,
            }
        ],
    )

    return fig


def _build_continent_groups(
    metric_data: pd.DataFrame,
    countries: list[str],
) -> dict[str, list[dict[str, object]]]:
    """Build continent groups with trace indices for HTML controls."""

    country_continents = (
        metric_data[["Country", "Continent"]]
        .drop_duplicates(subset=["Country"])
        .set_index("Country")["Continent"]
        .astype(str)
        .to_dict()
    )

    grouped: dict[str, list[dict[str, object]]] = {}

    for trace_index, country in enumerate(countries):
        continent = country_continents.get(country, "Other")
        continent = continent if continent.strip() else "Other"

        grouped.setdefault(continent, []).append(
            {
                "country": country,
                "trace_index": trace_index,
            }
        )

    ordered_continents = [
        continent
        for continent in CONTINENT_ORDER
        if continent in grouped
    ]

    ordered_continents.extend(
        sorted(
            continent
            for continent in grouped
            if continent not in ordered_continents
        )
    )

    return {
        continent: sorted(
            grouped[continent],
            key=lambda item: str(item["country"]),
        )
        for continent in ordered_continents
    }


def _build_checkbox_html(
    continent_groups: dict[str, list[dict[str, object]]],
) -> str:
    """Create continent-grouped checkbox markup."""

    sections: list[str] = []

    for group_index, (continent, entries) in enumerate(
        continent_groups.items()
    ):
        continent_id = f"continent-{group_index}"

        country_rows = "\n".join(
            f"""
            <label class="country-option">
                <input
                    type="checkbox"
                    class="country-checkbox"
                    data-trace-index="{entry['trace_index']}"
                    data-continent-id="{continent_id}"
                    checked
                >
                <span>{html.escape(str(entry['country']))}</span>
            </label>
            """
            for entry in entries
        )

        sections.append(
            f"""
            <section class="continent-group">
                <div class="continent-header">
                    <h3>{html.escape(continent)}</h3>
                    <div class="continent-actions">
                        <button
                            type="button"
                            class="continent-select"
                            data-continent-id="{continent_id}"
                        >
                            All
                        </button>
                        <button
                            type="button"
                            class="continent-clear"
                            data-continent-id="{continent_id}"
                        >
                            None
                        </button>
                    </div>
                </div>
                <div class="continent-countries" id="{continent_id}">
                    {country_rows}
                </div>
            </section>
            """
        )

    return "\n".join(sections)


def get_output_file(
    metric_config: dict[str, object],
) -> Path:
    """Return the website-ready output path for a metric."""

    labels = _build_chart_labels(metric_config)
    return OUTPUT_DIR / labels["output_slug"] / "index.html"


def save_trade_animation(
    fig: go.Figure,
    metric_data: pd.DataFrame,
    metric_config: dict[str, object],
) -> Path:
    """
    Save one metric visualization with continent-grouped controls.
    """

    labels = _build_chart_labels(metric_config)
    output_file = get_output_file(metric_config)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    countries = [str(trace.name) for trace in fig.data]
    continent_groups = _build_continent_groups(metric_data, countries)

    country_ranges: dict[str, dict[str, float]] = {}

    for country in countries:
        country_data = metric_data[
            metric_data["Country"] == country
        ]

        country_ranges[country] = {
            "x_max": float(country_data["X Value"].max()),
            "y_max": float(country_data["Y Value"].max()),
        }

    countries_json = json.dumps(countries)
    country_ranges_json = json.dumps(country_ranges)
    checkbox_html = _build_checkbox_html(continent_groups)

    plot_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        div_id="trade-chart",
        config={
            "responsive": True,
            "displaylogo": False,
        },
    )

    description_html = (
        f'<p class="metric-description">'
        f'{html.escape(labels["description"])}</p>'
        if labels["description"]
        else ""
    )

    page_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>{html.escape(labels['title'])}</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            background: #111111;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }}

        button,
        input {{
            font: inherit;
        }}

        .visualization-layout {{
            display: grid;
            grid-template-columns: 260px minmax(0, 1fr);
            min-height: 100vh;
        }}

        .country-panel {{
            padding: 20px;
            border-right: 1px solid #444444;
            background: #181818;
            overflow-y: auto;
        }}

        .country-panel h2 {{
            margin: 0 0 8px;
            font-size: 19px;
        }}

        .metric-description {{
            margin: 0 0 16px;
            color: #c4c4c4;
            font-size: 13px;
            line-height: 1.45;
        }}

        .country-actions {{
            display: flex;
            gap: 8px;
            margin-bottom: 18px;
        }}

        .country-actions button,
        .continent-actions button {{
            padding: 6px 9px;
            border: 1px solid #666666;
            border-radius: 5px;
            background: #2b2b2b;
            color: #ffffff;
            cursor: pointer;
        }}

        .country-actions button:hover,
        .continent-actions button:hover {{
            background: #3b3b3b;
        }}

        .continent-group {{
            padding: 12px 0;
            border-top: 1px solid #343434;
        }}

        .continent-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 9px;
        }}

        .continent-header h3 {{
            margin: 0;
            font-size: 15px;
        }}

        .continent-actions {{
            display: flex;
            gap: 5px;
        }}

        .continent-actions button {{
            padding: 3px 6px;
            font-size: 11px;
        }}

        .continent-countries {{
            display: flex;
            flex-direction: column;
            gap: 7px;
        }}

        .country-option {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 14px;
        }}

        .color-key {{
            display: grid;
            gap: 7px;
            padding: 12px 0 16px;
            border-top: 1px solid #343434;
        }}

        .color-key-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: #d7d7d7;
            font-size: 12px;
        }}

        .color-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex: 0 0 auto;
        }}

        .chart-container {{
            position: relative;
            min-width: 0;
            overflow: hidden;
        }}

        #year-watermark {{
            position: absolute;
            top: 55px;
            right: 70px;

            z-index: 2;

            font-size: 190px;
            font-weight: 500;
            line-height: 1;

            color: rgba(255, 255, 255, 0.08);

            pointer-events: none;
            user-select: none;
        }}

        #trade-chart {{
            width: 100%;
        }}

        @media (max-width: 800px) {{
            .visualization-layout {{
                grid-template-columns: 1fr;
            }}

            .country-panel {{
                border-right: 0;
                border-bottom: 1px solid #444444;
                max-height: 420px;
            }}

            .continent-countries {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(130px, 1fr));
            }}
        }}
    </style>
</head>

<body>
    <div class="visualization-layout">
        <aside class="country-panel">
            <h2>Select countries</h2>
            {description_html}

            <div class="country-actions">
                <button id="select-all" type="button">
                    Select all
                </button>
                <button id="clear-all" type="button">
                    Clear all
                </button>
            </div>

            <div class="color-key">
                <div class="color-key-row">
                    <span
                        class="color-dot"
                        style="background: {html.escape(X_PARTNER_COLOR)}"
                    ></span>
                    <span>{html.escape(labels['x_partner'])} is larger</span>
                </div>
                <div class="color-key-row">
                    <span
                        class="color-dot"
                        style="background: {html.escape(Y_PARTNER_COLOR)}"
                    ></span>
                    <span>{html.escape(labels['y_partner'])} is larger</span>
                </div>
            </div>

            <div class="country-list">
                {checkbox_html}
            </div>
        </aside>

        <main class="chart-container">
            <div id="year-watermark">{int(metric_data["Year"].min())}</div>
            {plot_html}
        </main>
    </div>

    <script>
        const chartId = "trade-chart";
        const countries = {countries_json};
        const countryRanges = {country_ranges_json};
        const axisPadding = {DEFAULT_AXIS_PADDING};

        const chart = document.getElementById(chartId);
        const yearWatermark = document.getElementById("year-watermark");

        function updateYearWatermark(year) {{
            yearWatermark.textContent = String(year);
        }}

        chart.on("plotly_sliderchange", (event) => {{
            if (event.step && event.step.label) {{
                updateYearWatermark(event.step.label);
            }}
        }});

        chart.on("plotly_animatingframe", (event) => {{
            if (event && event.name) {{
                updateYearWatermark(event.name);
            }}
        }});

        const checkboxes = document.querySelectorAll(
            ".country-checkbox"
        );

        function setTraceVisibility(traceIndex, isVisible) {{
            Plotly.restyle(
                chartId,
                {{ visible: isVisible }},
                [traceIndex]
            );
        }}

        function getSelectedCountries() {{
            return Array.from(checkboxes)
                .filter((checkbox) => checkbox.checked)
                .map((checkbox) => {{
                    const traceIndex = Number(
                        checkbox.dataset.traceIndex
                    );
                    return countries[traceIndex];
                }});
        }}

        function updateAxisRanges() {{
            const selectedCountries = getSelectedCountries();

            if (selectedCountries.length === 0) {{
                return;
            }}

            const xMax = Math.max(
                ...selectedCountries.map(
                    (country) => countryRanges[country].x_max
                )
            );

            const yMax = Math.max(
                ...selectedCountries.map(
                    (country) => countryRanges[country].y_max
                )
            );

            const paddedXMax = xMax * axisPadding;
            const paddedYMax = yMax * axisPadding;

            const equalityMax = Math.min(
                paddedXMax,
                paddedYMax
            );

            Plotly.relayout(
                chartId,
                {{
                    "xaxis.autorange": false,
                    "yaxis.autorange": false,

                    "xaxis.range": [0, paddedXMax],
                    "yaxis.range": [0, paddedYMax],

                    "shapes[0].x0": 0,
                    "shapes[0].y0": 0,
                    "shapes[0].x1": equalityMax,
                    "shapes[0].y1": equalityMax
                }}
            );
        }}

        function setCheckboxes(checkboxSet, isChecked) {{
            checkboxSet.forEach((checkbox) => {{
                checkbox.checked = isChecked;
                setTraceVisibility(
                    Number(checkbox.dataset.traceIndex),
                    isChecked
                );
            }});

            if (isChecked) {{
                updateAxisRanges();
            }} else if (getSelectedCountries().length > 0) {{
                updateAxisRanges();
            }}
        }}

        checkboxes.forEach((checkbox) => {{
            checkbox.addEventListener("change", () => {{
                setTraceVisibility(
                    Number(checkbox.dataset.traceIndex),
                    checkbox.checked
                );
                updateAxisRanges();
            }});
        }});

        document
            .getElementById("select-all")
            .addEventListener("click", () => {{
                setCheckboxes(Array.from(checkboxes), true);
            }});

        document
            .getElementById("clear-all")
            .addEventListener("click", () => {{
                setCheckboxes(Array.from(checkboxes), false);
            }});

        document
            .querySelectorAll(".continent-select")
            .forEach((button) => {{
                button.addEventListener("click", () => {{
                    const continentId = button.dataset.continentId;
                    const groupCheckboxes = Array.from(
                        document.querySelectorAll(
                            `.country-checkbox[data-continent-id="${{continentId}}"]`
                        )
                    );
                    setCheckboxes(groupCheckboxes, true);
                }});
            }});

        document
            .querySelectorAll(".continent-clear")
            .forEach((button) => {{
                button.addEventListener("click", () => {{
                    const continentId = button.dataset.continentId;
                    const groupCheckboxes = Array.from(
                        document.querySelectorAll(
                            `.country-checkbox[data-continent-id="${{continentId}}"]`
                        )
                    );
                    setCheckboxes(groupCheckboxes, false);
                }});
            }});
    </script>
</body>
</html>
"""

    output_file.write_text(page_html, encoding="utf-8")

    print(f"Animation saved to: {output_file.resolve()}")
    return output_file


def display_trade_animation(output_file: Path) -> None:
    """Open a saved visualization in the default browser."""

    webbrowser.open(output_file.resolve().as_uri())