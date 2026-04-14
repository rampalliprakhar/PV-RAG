import re
from patient.db import get_db_connection, init_db
from search import search

def save_log(date, foods, activities, skin_score, notes):
    init_db()
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO daily_logs (date, foods, activities, skin_score, notes) "
            "VALUES (?,?,?,?,?)",
            (date, foods, activities, int(skin_score), notes)
        )
        conn.commit()

def get_all_logs():
    init_db()
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_logs ORDER BY date DESC"
        ).fetchall()
    return [dict(r) for r in rows]

def cross_reference(foods_text):
    """
    For each food item, query the FAISS index for PV trigger literature.
    Returns markdown string.
    """
    if not foods_text.strip():
        return "No foods provided for cross-referencing."
    
    items = [f.strip() for f in re.split(r"[,\n;]+", foods_text) if f.strip()]
    if not items:
        return "Could not parse any food items from the input."
    
    output = []
    for item in items:
        hits = search(f"pemphigus vulgaris {item} trigger flare")[:3]
        if not hits:
            continue
        refs = []
        for h in hits:
            fname = h["path"].replace("\\", "/").split("/")[-1]
            snippet = h["content"][:180].replace("\n", " ")
            if fname.startswith("pmid_"):
                pmid = fname[5:].replace(".txt", "")
                link = f"[PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
            elif fname.startswith("pmc_"):
                pmc_id = fname[4:].replace(".txt", "")
                link = f"[PMC{pmc_id}](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/)"
            else:
                link = fname
            refs.append(f"  - {link}: _{snippet}…_")
        if refs:
            output.append(f"**{item.title()}**\n" + "\n".join(refs))

    return "\n\n".join(output) if output else "*No literature found for these items.*"