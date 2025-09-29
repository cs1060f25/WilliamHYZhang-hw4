# HW4: County Data API Prototype

This repository contains the code for Homework 4: API Prototyping with Generative AI. It includes:

- `csv_to_sqlite.py`: command-line utility to load arbitrary CSV files into a SQLite database.
- `api/`: Flask application that exposes the required `county_data` endpoint for serving county-level data from the generated SQLite database.
- Deployment configuration for Vercel.

## Setup

1. Create and activate a Python 3 virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Download the required CSV datasets to the project root:

- `zip_county.csv`
- `county_health_rankings.csv`

3. Generate the SQLite database using the provided script:

```bash
python csv_to_sqlite.py data.db zip_county.csv
python csv_to_sqlite.py data.db county_health_rankings.csv
```

4. Run the Flask development server locally:

```bash
python api/index.py
```

The API will be available at `http://localhost:5000`.

## csv_to_sqlite.py

The script accepts a target SQLite database file and an input CSV file. It

- Creates the database if it does not exist.
- Creates a table named after the CSV file (without extension) if it is missing.
- Inserts all records from the CSV into the corresponding table.
- Uses transactions and parameterized inserts to guard against SQL injection.

Example usage:

```bash
python csv_to_sqlite.py data.db zip_county.csv
```

## API Usage

- Endpoint: `POST /county_data`
- Request JSON body must include:
  - `zip`: 5-digit ZIP code
  - `measure_name`: one of the required measure strings in the assignment spec
- Optional JSON key `coffee` with value `teapot` forces an HTTP 418 response.

Example request:

```bash
curl -s -H 'content-type: application/json' \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  http://localhost:5000/county_data
```

Example response (truncated):

```json
[
  {
    "state": "MA",
    "county": "Middlesex County",
    "measure_name": "Adult obesity",
    "raw_value": "0.23",
    "data_release_year": "2012"
    // ...
  }
]
```

The repository includes `link.txt` which points to the deployed endpoint.

## Deployment

The project is configured for Vercel deployment using `vercel.json`. Deployments can run the Flask app using Gunicorn via a single entrypoint configured in the `api` directory.

## Attribution

Where applicable, inline comments in the source code note the origin of generated code snippets or external references.
