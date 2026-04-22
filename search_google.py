"""
Google Search via SearchAPI.io

Reads search queries from a text file, executes them via SearchAPI.io,
and exports results to a CSV file.
"""

import argparse
import csv
import os
import sys

import requests
from dotenv import load_dotenv


API_ENDPOINT = "https://www.searchapi.io/api/v1/search"


def load_queries(filepath: str) -> list[str]:
    """Read queries from a text file, one per line."""
    if not os.path.exists(filepath):
        print(f"Error: Input file '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        queries = [line.strip() for line in f if line.strip()]

    if not queries:
        print(f"Error: No queries found in '{filepath}'.")
        sys.exit(1)

    return queries


def search_google(query: str, api_key: str) -> list[dict]:
    """Call SearchAPI.io and return organic results."""
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "device": "desktop",
        "gl": "us",
    }

    try:
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"API error for query '{query}': {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Network error for query '{query}': {e}")
        return []

    data = response.json()
    organic_results = data.get("organic_results", [])

    results = []
    for item in organic_results:
        results.append({
            "query": query,
            "position": item.get("position", ""),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "domain": item.get("domain", ""),
            "snippet": item.get("snippet", ""),
            "date": item.get("date", ""),
        })

    return results


def save_to_csv(results: list[dict], output_path: str) -> None:
    """Write results to a CSV file."""
    if not results:
        print("No results to save.")
        return

    fieldnames = ["query", "position", "title", "link", "domain", "snippet", "date"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to '{output_path}'")


def main():
    parser = argparse.ArgumentParser(
        description="Search Google via SearchAPI.io and export results to CSV"
    )
    parser.add_argument(
        "-i", "--input",
        default="queries.txt",
        help="Input file with queries, one per line (default: queries.txt)"
    )
    parser.add_argument(
        "-o", "--output",
        default="results.csv",
        help="Output CSV file (default: results.csv)"
    )
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("SEARCHAPI_KEY")

    if not api_key:
        print("Error: SEARCHAPI_KEY not found in .env file.")
        print("Create a .env file with: SEARCHAPI_KEY=your_api_key_here")
        sys.exit(1)

    queries = load_queries(args.input)
    print(f"Loaded {len(queries)} queries from '{args.input}'")

    all_results = []
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Searching: {query}")
        results = search_google(query, api_key)
        all_results.extend(results)
        print(f"  Found {len(results)} results")

    save_to_csv(all_results, args.output)
    print(f"\nSummary: {len(queries)} queries, {len(all_results)} total results")


if __name__ == "__main__":
    main()
