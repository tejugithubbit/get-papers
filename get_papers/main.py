import argparse
import csv
import re
from typing import List, Dict
from Bio import Entrez

Entrez.email = "your_email@example.com"  # Replace with your email

def search_pubmed(query: str, retmax: int = 20) -> List[str]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

def fetch_details(ids: List[str]) -> str:
    ids_str = ",".join(ids)
    handle = Entrez.efetch(db="pubmed", id=ids_str, rettype="medline", retmode="text")
    records = handle.read()
    handle.close()
    return records

def parse_records(raw_data: str, debug: bool = False) -> List[Dict[str, str]]:
    from Bio import Medline
    from io import StringIO
    records = list(Medline.parse(StringIO(raw_data)))
    results = []

    for record in records:
        pubmed_id = record.get("PMID", "")
        title = record.get("TI", "")
        pub_date = record.get("DP", "")
        authors = record.get("AU", [])
        affiliations = record.get("AD", [])
        if not isinstance(affiliations, list):
            affiliations = [affiliations]

        companies = []
        email = ""
        non_academic_authors = []

        for aff in affiliations:
            if re.search(r'\b(Pharma|Biotech|Inc|Ltd|LLC|Therapeutics|Laboratories)\b', aff, re.IGNORECASE):
                companies.append(aff)
                match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', aff)
                if match:
                    email = match.group()
                non_academic_authors = authors

        if companies:
            results.append({
                "PubmedID": pubmed_id,
                "Title": title,
                "Publication Date": pub_date,
                "Non-academic Author(s)": "; ".join(non_academic_authors),
                "Company Affiliation(s)": "; ".join(companies),
                "Corresponding Author Email": email
            })

    return results

def write_csv(data: List[Dict[str, str]], file_name: str):
    keys = ["PubmedID", "Title", "Publication Date", "Non-academic Author(s)",
            "Company Affiliation(s)", "Corresponding Author Email"]
    with open(file_name, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed papers with pharma/biotech authors")
    parser.add_argument("query", type=str, help="PubMed query string")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-m", "--max-results", type=int, default=20, help="Maximum number of papers to fetch (default: 20)")

    args = parser.parse_args()

    ids = search_pubmed(args.query, retmax=args.max_results)
    if args.debug:
        print(f"Found {len(ids)} papers")

    raw_data = fetch_details(ids)
    parsed = parse_records(raw_data, debug=args.debug)

    if args.file:
        write_csv(parsed, args.file)
        print(f"✅ Results saved to '{args.file}'")
    else:
        for paper in parsed:
            print(paper)

if __name__ == "__main__":
    main()
