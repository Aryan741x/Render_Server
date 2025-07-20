# plag_algos/js_ast.py
from pyjsparser import PyJsParser
from difflib import SequenceMatcher
from itertools import combinations

_parser = PyJsParser()

def _node_types(src: str) -> list[str]:
    """Return flat list of AST node‑type strings for a JS snippet."""
    try:
        tree = _parser.parse(src)
    except Exception:
        return []                # syntax error → empty bag
    out: list[str] = []

    def walk(node):
        if isinstance(node, dict) and "type" in node:
            out.append(node["type"])
            for v in node.values():
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(tree)
    return out

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _node_types(a), _node_types(b)).ratio()

def matches(docs: list[dict], threshold: float = 0.6) -> list[dict]:
    """
    docs = [{fileName, text, ...}, ...]  ➜  [{source, target, similarity}, ...]
    """
    out = []
    for d1, d2 in combinations(docs, 2):
        sim = _similarity(d1["text"], d2["text"])
        if sim >= threshold:
            out.append(
                {
                    "source": d1.get("fileName", d1.get("fileId")),
                    "target": d2.get("fileName", d2.get("fileId")),
                    "similarity": round(sim, 4),
                }
            )
    return out
