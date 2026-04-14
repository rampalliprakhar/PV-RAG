import os
import time
import requests
import xml.etree.ElementTree as ET
from config import NCBI_EMAIL, NCBI_API_KEY

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def _base_params():
    p = {"email": NCBI_EMAIL}
    if NCBI_API_KEY:
        p["api_key"] = NCBI_API_KEY
    return p

def _delay():
    time.sleep(0.11 if NCBI_API_KEY else 0.34)

def search_pmc(query, max_results):
    oa_query = f"{query}[Title/Abstract] AND open access[filter]"
    params = {**_base_params(),
              "db": "pmc", "term": oa_query,
              "retmax": max_results, "retmode": "json"}
    r = requests.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]

def _parse_pmc_xml(xml_bytes):
    """
    Extract (title, body_text) from JATS XML returned by PMC efetch.
    Returns None if the article has no usable text.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    title_el = root.find(".//article-title")
    title = "".join(title_el.itertext()).strip() if title_el is not None else ""

    paras = []
    # Abstract paragraphs
    for p in root.findall(".//abstract//p"):
        t = "".join(p.itertext()).strip()
        if t:
            paras.append(t)
    # Body paragraphs (sections, results, discussion etc.)
    for p in root.findall(".//body//p"):
        t = "".join(p.itertext()).strip()
        if t:
            paras.append(t)

    if not paras:
        return None

    body = "\n\n".join(paras)
    return title, f"{title}\n\n{body}" if title else body

def save_full_texts(query, max_results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[PMC] Searching: {query!r}")
    ids = search_pmc(query, max_results)
    print(f"[PMC] {len(ids)} OA articles found")

    ids = [i for i in ids
           if not os.path.exists(os.path.join(output_dir, f"pmc_{i}.txt"))]
    print(f"[PMC] {len(ids)} new articles to fetch")

    saved = 0
    for idx, pmc_id in enumerate(ids, 1):
        params = {**_base_params(),
                  "db": "pmc", "id": pmc_id,
                  "rettype": "xml", "retmode": "xml"}
        try:
            r = requests.get(f"{EUTILS}/efetch.fcgi", params=params, timeout=60)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  [warn] PMC{pmc_id}: {e}")
            _delay()
            continue

        result = _parse_pmc_xml(r.content)
        if result:
            _, text = result
            path = os.path.join(output_dir, f"pmc_{pmc_id}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            saved += 1

        if idx % 50 == 0:
            print(f"  {idx}/{len(ids)} processed")
        _delay()

    print(f"[PMC] Done - {saved} articles saved to {output_dir}")