import pandas as pd

from src.config import (
    COUNTRY_METADATA_SHEET,
    METRIC_METADATA_SHEET,
    TRADE_DATA_SHEET,
    WORKBOOK_FILE,
)


def load_trade_data() -> pd.DataFrame:
    """
    Load the fully tidy trade-data sheet.
    """

    if not WORKBOOK_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found:\n{WORKBOOK_FILE}"
        )

    return pd.read_excel(
        WORKBOOK_FILE,
        sheet_name=TRADE_DATA_SHEET
    )


def load_metric_metadata() -> pd.DataFrame:
    """
    Load the metric configuration sheet.
    """

    if not WORKBOOK_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found:\n{WORKBOOK_FILE}"
        )

    return pd.read_excel(
        WORKBOOK_FILE,
        sheet_name=METRIC_METADATA_SHEET
    )


def load_country_metadata() -> pd.DataFrame:
    """
    Load the country metadata sheet.
    """

    if not WORKBOOK_FILE.exists():
        raise FileNotFoundError(
            f"Workbook not found:\n{WORKBOOK_FILE}"
        )

    return pd.read_excel(
        WORKBOOK_FILE,
        sheet_name=COUNTRY_METADATA_SHEET
    )


def load_all_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load all workbook sheets required by the project.
    """

    trade_data = load_trade_data()
    metric_metadata = load_metric_metadata()
    country_metadata = load_country_metadata()

    return (
        trade_data,
        metric_metadata,
        country_metadata,
    )