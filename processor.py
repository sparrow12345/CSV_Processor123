
import csv
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Callable, DefaultDict

AggFunc = Callable[[List[float]], float]


class CSVProcessor:
    """Load, filter, sort, aggregate and produce grouped reports."""

    def __init__(self, rows: List[Dict[str, str]], headers: List[str]) -> None:
        self.headers: List[str] = headers
        self.rows: List[Dict[str, str]] = rows
        if not self.headers:
            raise ValueError("CSV file is empty or invalid.")


    @classmethod
    def from_files(cls, file_paths: List[str]) -> "CSVProcessor":
        all_rows: List[Dict[str, str]] = []
        headers: List[str] | None = None

        for path in file_paths:
            with open(path, mode="r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if headers is None:
                    headers = reader.fieldnames
                    if not headers:
                        raise ValueError(f"Empty CSV: {path}")
                elif reader.fieldnames != headers:
                    raise ValueError(f"Headers mismatch in {path}")
                all_rows.extend(reader)

        if headers is None:
            raise ValueError("No files provided")
        return cls(all_rows, headers)


    def apply_filter(self, where: str) -> None:
        col, op, val = self._parse_condition(where)
        if col not in self.headers:
            raise ValueError(f"Column '{col}' not found in CSV.")

        ops: Dict[str, Callable[[Any, Any], bool]] = {
            ">": lambda a, b: float(a) > float(b),
            "<": lambda a, b: float(a) < float(b),
            "=": lambda a, b: a == b,
        }
        if op not in ops:
            raise ValueError(f"Invalid operator '{op}'. Supported: >, <, =.")

        self.rows = [r for r in self.rows if ops[op](r[col], val)]


    def apply_sort(self, order_by: str) -> None:
        col, direction = self._parse_condition(order_by, expected_op="=")
        if col not in self.headers:
            raise ValueError(f"Column '{col}' not found in CSV.")
        if direction not in ("asc", "desc"):
            raise ValueError("Sort direction must be 'asc' or 'desc'.")

        numeric = all(self._is_numeric(r[col]) for r in self.rows if r[col])

        def key(row: Dict[str, str]) -> Any:
            v = float(row[col]) if numeric else row[col]
            return v if direction == "asc" else (-v if numeric else v[::-1])

        self.rows.sort(key=key)


    _agg_functions: Dict[str, AggFunc] = {
        "avg": lambda vs: sum(vs) / len(vs) if vs else 0.0,
        "min": min,
        "max": max,
    }

    def apply_aggregate(self, aggregate: str) -> Tuple[str, float]:
        if not self.rows:
            raise ValueError("No rows to aggregate.")
        col, agg = self._parse_condition(aggregate, expected_op="=")
        if col not in self.headers:
            raise ValueError(f"Column '{col}' not found in CSV.")
        if not all(self._is_numeric(r[col]) for r in self.rows if r[col]):
            raise ValueError(f"Column '{col}' must be numeric for aggregation.")

        values = [float(r[col]) for r in self.rows if r[col]]
        func = self._agg_functions[agg]
        result = func(values)
        return agg, round(result, 2) if agg == "avg" else result


    _report_funcs: Dict[str, AggFunc] = {
        "average-rating": lambda vs: sum(vs) / len(vs) if vs else 0.0,
        "min-rating": min,
        "max-rating": max,
    }

    def grouped_report(self, report: str) -> List[Dict[str, Any]]:
        if report not in self._report_funcs:
            raise ValueError(
                f"Invalid report '{report}'. Supported: average-rating, min-rating, max-rating."
            )
        func = self._report_funcs[report]

        groups: DefaultDict[str, List[float]] = defaultdict(list)
        for row in self.rows:
            brand = row.get("brand")
            rating = row.get("rating")
            if brand and rating and self._is_numeric(rating):
                groups[brand].append(float(rating))

        result: List[Dict[str, Any]] = []
        # -----------------------------------------------------------------
        # NOTE: the loop must be *inside* the `for` that iterates over all
        #       brands – otherwise only the last brand is kept.
        # -----------------------------------------------------------------
        for brand, ratings in sorted(groups.items()):
            value = func(ratings)
            stat = report.replace("-rating", "")
            if stat == "average":
                value = round(value, 2)
            result.append({"brand": brand, stat: value})

        return result

    @staticmethod
    def _is_numeric(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _parse_condition(
        self, condition: str, expected_op: str | None = None
    ) -> Tuple[str, str, str]:
        if "=" in condition and (condition.count("=") == 1):
            # aggregate, order-by, report, or where with “=”
            col, rest = condition.split("=", 1)
            col = col.strip()
            # if the caller expects a specific operator we are done
            if expected_op:
                return col, rest.strip()
            # otherwise it is a where-filter with “=”
            return col, "=", rest.strip()

        # where-filter with “>” or “<”
        for op in (">", "<"):
            if op in condition:
                col, val = condition.split(op, 1)
                return col.strip(), op, val.strip()
        raise ValueError("Condition must contain >, < or =.")