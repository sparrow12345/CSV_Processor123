#!/usr/bin/env python3
import argparse
from typing import List
from tabulate import tabulate
from processor import CSVProcessor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSV processor – one --files argument, optional filter/aggregate/report."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="One or more CSV file paths",
    )
    parser.add_argument(
        "--where",
        help="Filter: column>value / column<value / column=value",
    )
    parser.add_argument(
        "--aggregate",
        help="Simple aggregate: column=avg/min/max",
    )
    parser.add_argument(
        "--order-by",
        help="Sort: column=asc / column=desc",
    )
    parser.add_argument(
        "--report",
        choices=["average-rating", "min-rating", "max-rating"],
        help="Grouped statistic on rating per brand",
    )

    args = parser.parse_args()

    try:
        # -----------------------------------------------------------------
        # 1. Load the CSV files
        # -----------------------------------------------------------------
        proc = CSVProcessor.from_files(args.files)

        # -----------------------------------------------------------------
        # 2. Apply optional operations (order matters!)
        # -----------------------------------------------------------------
        if args.where:
            proc.apply_filter(args.where)

        if args.order_by:
            proc.apply_sort(args.order_by)

        # -----------------------------------------------------------------
        # 3. Produce the requested output
        # -----------------------------------------------------------------
        if args.report:
            # grouped report → list of dicts: {"brand": ..., "average": ...}
            data = proc.grouped_report(args.report)
            stat_name = args.report.replace("-rating", "")
            headers = ["brand", stat_name]
            rows = [[row["brand"], row[stat_name]] for row in data]
            print(tabulate(rows, headers=headers, tablefmt="grid"))

        elif args.aggregate:
            # simple aggregate → (type, value)
            agg_type, value = proc.apply_aggregate(args.aggregate)
            print(tabulate([[value]], headers=[agg_type], tablefmt="grid"))

        else:
            # full table – list of dicts
            print(tabulate(proc.rows, headers="keys", tablefmt="grid"))

    # -----------------------------------------------------------------
    # 4. Friendly error handling (required for extra points)
    # -----------------------------------------------------------------
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError as e:
        print(f"Error: File not found – {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()