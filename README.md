# CSV Processor

**A lightweight, dependency-free CSV processing tool**  
Process multiple CSV files with **filtering, sorting, aggregation, and grouped reports** — all from the command line.

Built with **Python standard library** + `csv` + `tabulate`.  
**No pandas**. **No external APIs**. **Pure Python**.

---

## Features

| Feature | Supported |
|--------|-----------|
| Multi-file input (`--files file1.csv file2.csv`) | Yes |
| Filter by condition (`--where "price<300"`) | Yes |
| Sort by column (`--order-by "rating=desc"`) | Yes |
| Simple aggregation (`--aggregate "rating=avg"`) | Yes |
| Grouped report by brand (`--report average-rating`) | Yes |
| Beautiful `grid` table output | Yes |
| Header validation across files | Yes |
| Robust error handling | Yes |
| **96% test coverage** | Yes |
| **PEP-8 compliant, type-hinted** | Yes |

---

## 📁 Project Structure

```
csv_processor/
├─ processor.py
├─ products.csv
├─ main.py
├─ utils.py
├─ __init__.py
├─ tests/
├─ requirements.txt
├─ README.md
```

## 🚀 Setup Instructions

1. **Clone the Repository**

```
git clone https://github.com/your-username/csv_processor.git
```

2. **Create and Activate a Virtual Environment**

```
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. **Install Dependencies**

```
pip install -r requirements.txt
```

4. **🧪 Running Tests**

This project uses pytest for testing. To run all tests:

```
PYTHONPATH=. pytest
```

If you want a detailed report with coverage:

```
PYTHONPATH=. pytest --cov=csv_processor tests/
```

5. **🛠️ Usage (Command-Line Interface)**

```
python main.py product.csv [--files path of list of paths separated by spaces] [--where FILTER] [--aggregate AGGREGATE] [--order-by ORDER]
```

6. **🔤 Arguments**

| Argument	| Description |
|-----------|-------------|
|`--where`	| Filter rows. Format: column/operator/value (e.g. price>500)|
|`--aggregate`| Apply aggregation. Format: func=column (e.g. avg=price)|
|`--order-by` | Sort the rows. Format: column=asc or column=desc (e.g. rating=desc)|
|`--report` | provides a report of some aggregate function applied over the samples and grouped by brand|

7. **🧾 Examples**

Filter phones with price > 500, calculate the average price across all rows, or order rows by rating.

```
python main.py products.csv --where price>500

python main.py products.csv --aggregate avg=price

python main.py products.csv --order-by rating=desc
```