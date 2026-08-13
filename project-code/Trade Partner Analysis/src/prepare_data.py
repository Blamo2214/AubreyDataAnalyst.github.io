import pandas as pd


TRADE_REQUIRED_COLUMNS = {
    "Year",
    "Country",
    "Continent",
    "Metric",
    "Partner",
    "Value",
    "Unit",
}

METRIC_REQUIRED_COLUMNS = {
    "Metric",
    "Display Name",
    "Description",
    "Default X Partner",
    "Default Y Partner",
    "Value Format",
    "Axis Suffix",
    "Output Slug",
    "Enabled",
}

COUNTRY_REQUIRED_COLUMNS = {
    "Country",
    "Continent",
    "Enabled",
}


def _validate_required_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    sheet_name: str,
) -> None:
    """
    Confirm that a workbook sheet contains all required columns.
    """

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise KeyError(
            f"{sheet_name} is missing these columns: "
            + ", ".join(sorted(missing_columns))
        )


def _is_enabled(value: object) -> bool:
    """
    Interpret common spreadsheet values as enabled or disabled.
    """

    return str(value).strip().lower() in {
        "yes",
        "true",
        "1",
        "enabled",
    }


def clean_trade_data(
    trade_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate and clean the fully tidy trade dataset.
    """

    _validate_required_columns(
        trade_data,
        TRADE_REQUIRED_COLUMNS,
        "Trade Data",
    )

    trade_data = trade_data.copy()

    trade_data["Year"] = pd.to_numeric(
        trade_data["Year"],
        errors="coerce",
    )

    trade_data["Value"] = pd.to_numeric(
        trade_data["Value"],
        errors="coerce",
    )

    text_columns = [
        "Country",
        "Continent",
        "Metric",
        "Partner",
        "Unit",
    ]

    for column in text_columns:
        trade_data[column] = (
            trade_data[column]
            .astype("string")
            .str.strip()
        )

    trade_data = trade_data.dropna(
        subset=[
            "Year",
            "Country",
            "Continent",
            "Metric",
            "Partner",
            "Value",
            "Unit",
        ]
    )

    trade_data["Year"] = trade_data["Year"].astype(int)

    duplicate_columns = [
        "Year",
        "Country",
        "Metric",
        "Partner",
    ]

    duplicates = trade_data.duplicated(
        subset=duplicate_columns,
        keep=False,
    )

    if duplicates.any():
        duplicate_rows = trade_data.loc[
            duplicates,
            duplicate_columns,
        ]

        raise ValueError(
            "Duplicate trade observations were found:\n"
            f"{duplicate_rows.to_string(index=False)}"
        )

    return (
        trade_data
        .sort_values(
            [
                "Metric",
                "Year",
                "Country",
                "Partner",
            ]
        )
        .reset_index(drop=True)
    )


def clean_metric_metadata(
    metric_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate and clean metric-level chart settings.
    """

    _validate_required_columns(
        metric_metadata,
        METRIC_REQUIRED_COLUMNS,
        "Metric Metadata",
    )

    metric_metadata = metric_metadata.copy()

    text_columns = [
        "Metric",
        "Display Name",
        "Description",
        "Default X Partner",
        "Default Y Partner",
        "Value Format",
        "Axis Suffix",
        "Output Slug",
    ]

    for column in text_columns:
        metric_metadata[column] = (
            metric_metadata[column]
            .astype("string")
            .fillna("")
            .str.strip()
        )

    metric_metadata["Enabled"] = metric_metadata[
        "Enabled"
    ].apply(_is_enabled)

    duplicate_metrics = metric_metadata["Metric"].duplicated(
        keep=False
    )

    if duplicate_metrics.any():
        duplicate_names = metric_metadata.loc[
            duplicate_metrics,
            "Metric",
        ].tolist()

        raise ValueError(
            "Duplicate metric metadata rows were found: "
            + ", ".join(duplicate_names)
        )

    return metric_metadata.reset_index(drop=True)


def clean_country_metadata(
    country_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Validate and clean country-level metadata.
    """

    _validate_required_columns(
        country_metadata,
        COUNTRY_REQUIRED_COLUMNS,
        "Country Metadata",
    )

    country_metadata = country_metadata.copy()

    country_metadata["Country"] = (
        country_metadata["Country"]
        .astype("string")
        .str.strip()
    )

    country_metadata["Continent"] = (
        country_metadata["Continent"]
        .astype("string")
        .str.strip()
    )

    country_metadata["Enabled"] = country_metadata[
        "Enabled"
    ].apply(_is_enabled)

    duplicate_countries = country_metadata[
        "Country"
    ].duplicated(
        keep=False
    )

    if duplicate_countries.any():
        duplicate_names = country_metadata.loc[
            duplicate_countries,
            "Country",
        ].tolist()

        raise ValueError(
            "Duplicate country metadata rows were found: "
            + ", ".join(duplicate_names)
        )

    return country_metadata.reset_index(drop=True)


def get_enabled_metrics(
    metric_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Return only metrics marked as enabled.
    """

    return (
        metric_metadata[
            metric_metadata["Enabled"]
        ]
        .copy()
        .reset_index(drop=True)
    )


def get_metric_config(
    metric_metadata: pd.DataFrame,
    metric_name: str,
) -> dict[str, object]:
    """
    Return one metric's metadata as a dictionary.
    """

    matching_rows = metric_metadata[
        metric_metadata["Metric"] == metric_name
    ]

    if matching_rows.empty:
        raise KeyError(
            f"No metadata row was found for metric: "
            f"{metric_name}"
        )

    return matching_rows.iloc[0].to_dict()


def prepare_metric_data(
    trade_data: pd.DataFrame,
    country_metadata: pd.DataFrame,
    metric_config: dict[str, object],
) -> pd.DataFrame:
    """
    Prepare one metric and partner pair for the animated chart.

    Output columns:
        Year
        Country
        Continent
        X Value
        Y Value
    """

    metric_name = str(metric_config["Metric"])
    x_partner = str(metric_config["Default X Partner"])
    y_partner = str(metric_config["Default Y Partner"])

    enabled_countries = country_metadata.loc[
        country_metadata["Enabled"],
        [
            "Country",
            "Continent",
        ],
    ].copy()

    metric_data = trade_data[
        (trade_data["Metric"] == metric_name)
        & trade_data["Partner"].isin(
            [
                x_partner,
                y_partner,
            ]
        )
    ].copy()

    metric_data = metric_data.merge(
        enabled_countries,
        on="Country",
        how="inner",
        suffixes=("_trade", "_metadata"),
    )

    continent_mismatch = (
        metric_data["Continent_trade"]
        != metric_data["Continent_metadata"]
    )

    if continent_mismatch.any():
        mismatches = metric_data.loc[
            continent_mismatch,
            [
                "Country",
                "Continent_trade",
                "Continent_metadata",
            ],
        ].drop_duplicates()

        raise ValueError(
            "Continent values disagree between Trade Data "
            "and Country Metadata:\n"
            f"{mismatches.to_string(index=False)}"
        )

    pivoted = (
        metric_data.pivot(
            index=[
                "Year",
                "Country",
                "Continent_metadata",
            ],
            columns="Partner",
            values="Value",
        )
        .reset_index()
        .rename(
            columns={
                "Continent_metadata": "Continent",
                x_partner: "X Value",
                y_partner: "Y Value",
            }
        )
    )

    required_partner_columns = {
        "X Value",
        "Y Value",
    }

    missing_partner_columns = (
        required_partner_columns.difference(
            pivoted.columns
        )
    )

    if missing_partner_columns:
        raise ValueError(
            f"Metric '{metric_name}' is missing data for "
            f"one or both configured partners: "
            f"{x_partner}, {y_partner}"
        )

    pivoted = pivoted.dropna(
        subset=[
            "Year",
            "Country",
            "Continent",
            "X Value",
            "Y Value",
        ]
    )

    pivoted["Year"] = pivoted["Year"].astype(int)

    return (
        pivoted
        .sort_values(
            [
                "Year",
                "Continent",
                "Country",
            ]
        )
        .reset_index(drop=True)
    )