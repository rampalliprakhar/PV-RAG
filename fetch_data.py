import requests
import argparse
from fetchers.pubmed import save_abstracts
from fetchers.pmc import save_full_texts
from config import (PV_QUERY,
                    PUBMED_MAX_RESULTS, PMC_MAX_RESULTS,
                    PUBMED_DATA_FOLDER, PMC_DATA_FOLDER)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch pemphigus vulgaris literature from NCBI")
    parser.add_argument("--pubmed", action="store_true",
                        help="Fetch PubMed abstracts only")
    parser.add_argument("--pmc",    action="store_true",
                        help="Fetch PMC full-text only")
    args = parser.parse_args()

    run_pubmed = args.pubmed or not (args.pubmed or args.pmc)
    run_pmc    = args.pmc    or not (args.pubmed or args.pmc)

    if run_pubmed:
        save_abstracts(PV_QUERY, PUBMED_MAX_RESULTS, PUBMED_DATA_FOLDER)
    if run_pmc:
        save_full_texts(PV_QUERY, PMC_MAX_RESULTS, PMC_DATA_FOLDER)


if __name__ == "__main__":
    main()