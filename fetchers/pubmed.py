import os
import time
import requests
import xml.etree.ElementTree as ET
from config import NCBI_EMAIL, NCBI_API_KEY

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BATCH  = 500   # NCBI max per efetch call

def _base_params():
    p = {"email": NCBI_EMAIL}
    if NCBI_API_KEY:
        p["api_key"] = NCBI_API_KEY
    return p

def _delay():
    # NCBI rate limits: 10/s with key, 3/s without
    time.sleep(0.11 if NCBI_API_KEY else 0.34)

def search_pubmed(query, max_results):
    params = {**_base_params(),
              "db": "pubmed", "term": query,
              "retmax": max_results, "retmode": "json"}
    r = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

def _parse_batch_xml(xml_bytes):
    """Yield (pmid, title, abstract) from a PubMed efetch XML response."""
    root = ET.fromstring(xml_bytes)
    for article in root.findall(".//PubmedArticle"):
        pmid_el  = article.find(".//PMID")
        title_el = article.find(".//ArticleTitle")
        pmid  = pmid_el.text  if pmid_el  is not None else "unknown"
        title = "".join(title_el.itertext()) if title_el is not None else ""

        parts = []
        for at in article.findall(".//AbstractText"):
            label = at.get("Label", "")
            text  = "".join(at.itertext()).strip()
            parts.append(f"{label}: {text}" if label else text)
        abstract = " ".join(parts).strip()

        if abstract:
            yield pmid, title, abstract

def save_abstracts(query, max_results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[PubMed] Searching: {query!r}")
    ids = search_pubmed(query, max_results)
    print(f"[PubMed] {len(ids)} articles found")

    # Resume: skip already saved
    ids = [i for i in ids
           if not os.path.exists(os.path.join(output_dir, f"pmid_{i}.txt"))]
    print(f"[PubMed] {len(ids)} new abstracts to fetch")

    saved = 0
    for start in range(0, len(ids), BATCH):
        batch = ids[start:start + BATCH]
        params = {**_base_params(),
                  "db": "pubmed", "id": ",".join(batch),
                  "rettype": "abstract", "retmode": "xml"}
        try:
            r = requests.get(f"{EUTILS}/efetch.fcgi", params=params, timeout=60)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  [warn] batch {start}: {e}")
            _delay()
            continue

        for pmid, title, abstract in _parse_batch_xml(r.content):
            path = os.path.join(output_dir, f"pmid_{pmid}.txt")
            with open(path, "w", encoding="utf-8") as f:
                if title:
                    f.write(title + "\n\n")
                f.write(abstract)
            saved += 1

        print(f"  {min(start + BATCH, len(ids))}/{len(ids)} processed")
        _delay()

    print(f"[PubMed] Done - {saved} abstracts saved to {output_dir}")