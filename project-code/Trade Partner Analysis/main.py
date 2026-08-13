from src.load_data import load_all_data
from src.prepare_data import (
    clean_country_metadata,
    clean_metric_metadata,
    clean_trade_data,
    get_enabled_metrics,
    get_metric_config,
    prepare_metric_data,
)
from src.visualization import (
    create_trade_animation,
    display_trade_animation,
    save_trade_animation,
)


def main() -> None:
    # -----------------------------------------------------
    # Load the workbook sheets
    # -----------------------------------------------------

    (
        trade_data,
        metric_metadata,
        country_metadata,
    ) = load_all_data()

    # -----------------------------------------------------
    # Clean and validate the data
    # -----------------------------------------------------

    trade_data = clean_trade_data(
        trade_data
    )

    metric_metadata = clean_metric_metadata(
        metric_metadata
    )

    country_metadata = clean_country_metadata(
        country_metadata
    )

    # -----------------------------------------------------
    # Build every enabled metric visualization
    # -----------------------------------------------------

    enabled_metrics = get_enabled_metrics(
        metric_metadata
    )

    if enabled_metrics.empty:
        raise ValueError(
            "No metrics are marked as enabled in "
            "the Metric Metadata sheet."
        )

    generated_files = []

    for metric_name in enabled_metrics["Metric"]:
        metric_config = get_metric_config(
            metric_metadata,
            metric_name,
        )

        chart_data = prepare_metric_data(
            trade_data,
            country_metadata,
            metric_config,
        )

        if chart_data.empty:
            print(
                f"Skipping {metric_name}: "
                "no complete China and U.S. observations were found."
            )
            continue

        country_count = chart_data["Country"].nunique()
        year_count = chart_data["Year"].nunique()
        observation_count = len(chart_data)

        first_year = int(chart_data["Year"].min())
        last_year = int(chart_data["Year"].max())

        figure = create_trade_animation(
            chart_data,
            metric_config,
        )

        output_file = save_trade_animation(
            figure,
            chart_data,
            metric_config,
        )

        generated_files.append(
            output_file
        )

        print()
        print(metric_name)
        print(f"  Countries: {country_count}")
        print(
            f"  Years: {first_year}-{last_year} "
            f"({year_count} years)"
        )
        print(f"  Observations: {observation_count:,}")
        print(f"  Output: {output_file}")

    # -----------------------------------------------------
    # Open the first generated visualization
    # -----------------------------------------------------

    if not generated_files:
        raise ValueError(
            "No visualization files were generated."
        )

    display_trade_animation(
        generated_files[0]
    )

    print()
    print("-" * 50)
    print(
        f"Generated {len(generated_files)} "
        "visualization(s) successfully."
    )


if __name__ == "__main__":
    main()