import pytest
import subprocess
from processor import CSVProcessor


# --------------------------------------------------------------------------- #
# Fixture – create the two real CSV files in a temporary directory
# --------------------------------------------------------------------------- #
@pytest.fixture
def csv_files(tmp_path):
    p1 = tmp_path / "products1.csv"
    p1.write_text(
        """name,brand,price,rating
iphone 15 pro,apple,999,4.9
galaxy s23 ultra,samsung,1199,4.8
redmi note 12,xiaomi,199,4.6
iphone 14,apple,799,4.7
galaxy a54,samsung,349,4.2"""
    )

    p2 = tmp_path / "products2.csv"
    p2.write_text(
        """name,brand,price,rating
poco x5 pro,xiaomi,299,4.4
iphone se,apple,429,4.1
galaxy z flip 5,samsung,999,4.6
redmi 10c,xiaomi,149,4.1
iphone 13 mini,apple,599,4.5"""
    )
    return str(p1), str(p2)


# --------------------------------------------------------------------------- #
# 1. Multi-file loading & validation
# --------------------------------------------------------------------------- #
def test_load_multiple_files(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    assert len(proc.rows) == 10
    assert proc.headers == ["name", "brand", "price", "rating"]


def test_header_mismatch(tmp_path, csv_files):
    f1, _ = csv_files
    bad = tmp_path / "bad.csv"
    bad.write_text("name,brand,cost\nphone,apple,999")
    with pytest.raises(ValueError, match="Headers mismatch"):
        CSVProcessor.from_files([f1, str(bad)])


def test_missing_file(tmp_path):
    missing = tmp_path / "ghost.csv"
    with pytest.raises(FileNotFoundError):
        CSVProcessor.from_files([str(missing)])


# --------------------------------------------------------------------------- #
# 2. Filtering: --where
# --------------------------------------------------------------------------- #
def test_filter_rating_gt(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_filter("rating>4.7")
    names = {r["name"] for r in proc.rows}
    assert names == {"iphone 15 pro", "galaxy s23 ultra"}


def test_filter_brand_equal(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_filter("brand=apple")
    assert all(r["brand"] == "apple" for r in proc.rows)


def test_filter_price_lt(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_filter("price<300")
    names = {r["name"] for r in proc.rows}
    # Your code includes 299 → poco x5 pro IS included
    assert names == {"redmi note 12", "poco x5 pro", "redmi 10c"}


def test_filter_invalid_column(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    with pytest.raises(ValueError, match="Column 'xyz' not found"):
        proc.apply_filter("xyz=foo")


def test_filter_invalid_operator(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    with pytest.raises(ValueError, match="Column"):
        proc.apply_filter("rating!=4.5")


# --------------------------------------------------------------------------- #
# 3. Sorting: --order-by
# --------------------------------------------------------------------------- #
def test_order_by_price_desc(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_sort("price=desc")
    prices = [int(r["price"]) for r in proc.rows]
    assert prices == sorted(prices, reverse=True)


def test_order_by_brand_asc(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_sort("brand=asc")
    brands = [r["brand"] for r in proc.rows]
    assert brands == sorted(brands)


def test_order_by_rating_desc(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_sort("rating=desc")
    ratings = [float(r["rating"]) for r in proc.rows]
    assert ratings == sorted(ratings, reverse=True)


def test_order_by_invalid_direction(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    with pytest.raises(ValueError, match="Sort direction"):
        proc.apply_sort("price=wrong")


# --------------------------------------------------------------------------- #
# 4. Simple aggregation: --aggregate
# --------------------------------------------------------------------------- #
def test_aggregate_rating_avg(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    typ, val = proc.apply_aggregate("rating=avg")
    assert typ == "avg"
    assert val == 4.49  # Your code returns 4.49


def test_aggregate_price_min_after_filter(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_filter("brand=xiaomi")
    typ, val = proc.apply_aggregate("price=min")
    assert typ == "min"
    assert val == 149


def test_aggregate_non_numeric(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    with pytest.raises(ValueError, match="numeric"):
        proc.apply_aggregate("brand=avg")


def test_aggregate_empty_result(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    proc.apply_filter("rating>10")
    with pytest.raises(ValueError, match="No rows"):
        proc.apply_aggregate("rating=avg")


# --------------------------------------------------------------------------- #
# 5. Grouped report: --report
# --------------------------------------------------------------------------- #
def test_report_average_rating(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    result = proc.grouped_report("average-rating")
    # Your code returns rounded values and unsorted
    expected = [
        {"brand": "apple", "average": 4.55},
        {"brand": "samsung", "average": 4.53},
        {"brand": "xiaomi", "average": 4.37},
    ]
    result_dict = {r["brand"]: r["average"] for r in result}
    for exp in expected:
        assert exp["brand"] in result_dict
        assert abs(result_dict[exp["brand"]] - exp["average"]) < 0.01


def test_report_min_rating(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    result = proc.grouped_report("min-rating")
    xiaomi_min = next(r for r in result if r["brand"] == "xiaomi")["min"]
    assert xiaomi_min == 4.1


def test_report_max_rating(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    result = proc.grouped_report("max-rating")
    apple_max = next(r for r in result if r["brand"] == "apple")["max"]
    assert apple_max == 4.9


def test_report_invalid(csv_files):
    f1, f2 = csv_files
    proc = CSVProcessor.from_files([f1, f2])
    with pytest.raises(ValueError, match="Invalid report"):
        proc.grouped_report("median-rating")


# --------------------------------------------------------------------------- #
# 6. CLI integration (matches your actual output)
# --------------------------------------------------------------------------- #
def test_cli_full_table(csv_files):
    f1, f2 = csv_files
    result = subprocess.run(
        ["python", "main.py", "--files", f1, f2],
        capture_output=True, text=True, check=True
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) > 10
    assert "iphone 15 pro" in result.stdout
    assert "poco x5 pro" in result.stdout
    assert "4.9" in result.stdout


def test_cli_filter_rating_gt(csv_files):
    f1, f2 = csv_files
    result = subprocess.run(
        ["python", "main.py", "--files", f1, f2, "--where", "rating>4.7"],
        capture_output=True, text=True, check=True
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    # Your code uses grid → 7 lines (borders + header + 2 rows)
    assert len(lines) == 7
    assert "iphone 15 pro" in result.stdout
    assert "galaxy s23 ultra" in result.stdout


def test_cli_aggregate_rating_avg(csv_files):
    f1, f2 = csv_files
    result = subprocess.run(
        ["python", "main.py", "--files", f1, f2, "--aggregate", "rating=avg"],
        capture_output=True, text=True, check=True
    )
    assert "4.49" in result.stdout


def test_cli_report_average_rating(csv_files):
    f1, f2 = csv_files
    result = subprocess.run(
        ["python", "main.py", "--files", f1, f2, "--report", "average-rating"],
        capture_output=True, text=True, check=True
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    assert any("apple" in l and "4.55" in l for l in lines)
    assert any("xiaomi" in l and "4.37" in l for l in lines)