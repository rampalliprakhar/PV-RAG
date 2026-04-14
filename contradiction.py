import re

_NEG = re.compile(
    r"\b(no|not|without|lack|absence|failed|ineffective|"
    r"no evidence|does not|cannot|rarely|not associated|no significant)\b", re.I
)
_POS = re.compile(
    r"\b(significant|effective|associated|proven|demonstrated|"
    r"causes|triggers|induces|increases|linked|correlates)\b", re.I
)

def detect(chunks):
    """
    Scan retrieved chunks for pairs where one makes a positive claim
    and another makes a negative/opposing claim about the same topic.
    Returns list of (chunk_a, chunk_b).
    """
    contradictions = []
    for i, a in enumerate(chunks):
        for b in chunks[i + 1:]:
            a_pos = bool(_POS.search(a["content"]))
            a_neg = bool(_NEG.search(a["content"]))
            b_pos = bool(_POS.search(b["content"]))
            b_neg = bool(_NEG.search(b["content"]))
            if (a_pos and not a_neg) and (b_neg and not b_pos):
                contradictions.append((a, b))
            elif (a_neg and not a_pos) and (b_pos and not b_neg):
                contradictions.append((b, a))
    return contradictions

def format_contradictions(chunks):
    pairs = detect(chunks)
    if not pairs:
        return "*No contradictions detected in these sources.*"
    parts = []
    for pos_chunk, neg_chunk in pairs:
        def _label(c):
            fname = c["path"].replace("\\", "/").split("/")[-1]
            if fname.startswith("pmid_"):
                pid = fname[5:].replace(".txt", "")
                return f"[PMID {pid}](https://pubmed.ncbi.nlm.nih.gov/{pid}/)"
            if fname.startswith("pmc_"):
                pid = fname[4:].replace(".txt", "")
                return f"[PMC{pid}](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pid}/)"
            return fname
        parts.append(
            f"**Supports:** {_label(pos_chunk)}\n"
            f"> {pos_chunk['content'][:220]}…\n\n"
            f"**Conflicts:** {_label(neg_chunk)}\n"
            f"> {neg_chunk['content'][:220]}…"
        )
    return "\n\n---\n\n".join(parts)