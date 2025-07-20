from difflib import SequenceMatcher
from itertools import combinations
from typing import List, Dict

import javalang


def _ast_token_seq(code: str) -> List[str]:
    """
    Parse Java source into an ordered list of node‑type names.
    If parsing fails (e.g., incomplete code) we return an empty list.
    """
    try:
        tree = javalang.parse.parse(code)
    except (javalang.parser.JavaSyntaxError, IndexError, TypeError):
        return []

    tokens: List[str] = []

    # javalang tree nodes are iterable – depth‑first walk
    for path, node in tree:
        tokens.append(type(node).__name__)

    return tokens


def _similarity(seq1: List[str], seq2: List[str]) -> float:
    """
    Simple SequenceMatcher ratio over AST node‑type lists.
    """
    return SequenceMatcher(None, seq1, seq2).ratio() if seq1 and seq2 else 0.0


def matches(
    docs: List[Dict], threshold: float = 0.6
) -> List[Dict]:
    """
    docs -> list of { fileName, userId, fileId, text }
    returns -> list of { source, target, similarity }
    """
    results: List[Dict] = []

    # Pre‑tokenise once per document
    ast_cache = {d["fileId"]: _ast_token_seq(d["text"]) for d in docs}

    for d1, d2 in combinations(docs, 2):
        s = _similarity(ast_cache[d1["fileId"]], ast_cache[d2["fileId"]])
        if s >= threshold:
            results.append(
                {
                    "source": d1["fileName"],
                    "target": d2["fileName"],
                    "similarity": round(s, 4),
                }
            )

    return results
