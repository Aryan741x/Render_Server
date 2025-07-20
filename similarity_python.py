import ast
import tokenize
from io import BytesIO
from difflib import SequenceMatcher
from itertools import combinations
from networkx.algorithms.similarity import graph_edit_distance
import networkx as nx


def _ast_similarity(code1: str, code2: str) -> float:
    try:
        tree1, tree2 = ast.parse(code1), ast.parse(code2)
    except SyntaxError as e:
        print(f"AST parse error: {e}")
        return 0.0
    n1 = [type(n).__name__ for n in ast.walk(tree1)]
    n2 = [type(n).__name__ for n in ast.walk(tree2)]
    ratio = SequenceMatcher(None, n1, n2).ratio()
    print(f"AST similarity: {ratio:.4f}")
    return ratio


def _tokenize(code: str):
    toks = []
    try:
        for tok in tokenize.tokenize(BytesIO(code.encode()).readline):
            if tok.type == tokenize.NAME:
                toks.append("ID")
            elif tok.type == tokenize.OP:
                toks.append(tok.string)
            elif tok.type in (tokenize.NUMBER, tokenize.STRING):
                toks.append(str(tok.type))
    except tokenize.TokenError as e:
        print(f"Tokenize error: {e}")
    return toks


def _token_similarity(c1: str, c2: str) -> float:
    t1, t2 = set(_tokenize(c1)), set(_tokenize(c2))
    sim = len(t1 & t2) / len(t1 | t2) if t1 | t2 else 0.0
    print(f"Token similarity: {sim:.4f}")
    return sim


class _CFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.graph = nx.DiGraph()
        self._cur = None
        self._idx = 0

    def _add(self, label):
        nid = self._idx
        self.graph.add_node(nid, label=label)
        if self._cur is not None:
            self.graph.add_edge(self._cur, nid)
        self._cur = nid
        self._idx += 1

    def visit_FunctionDef(self, n): self._add("Func"); self.generic_visit(n)
    def visit_If(self, n):          self._add("If");   self.generic_visit(n)
    def visit_For(self, n):         self._add("For");  self.generic_visit(n)
    def visit_While(self, n):       self._add("While");self.generic_visit(n)
    def visit_Return(self, n):      self._add("Ret")


def _cfg(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"CFG parse error: {e}")
        return nx.DiGraph()
    b = _CFGBuilder()
    b.visit(tree)
    return b.graph


def _cfg_similarity(c1: str, c2: str) -> float:
    g1, g2 = _cfg(c1), _cfg(c2)
    dist = graph_edit_distance(g1, g2)
    sim = 1 / (1 + dist) if dist is not None else 0.0
    print(f"CFG similarity: {sim:.4f}")
    return sim


def _weighted(ast_s, tok_s, cfg_s, w=(0.4, 0.4, 0.2)) -> float:
    score = w[0] * ast_s + w[1] * tok_s + w[2] * cfg_s
    print(f"Weighted similarity: {score:.4f}")
    return score


def python_matches(docs: list[dict], threshold: float = 0.7) -> list[dict]:
    print("Starting python_matches computation...")
    matches: list[dict] = []
    for idx, (d1, d2) in enumerate(combinations(docs, 2)):
        print(f"\nComparing pair {idx + 1}: {d1.get('userId')} vs {d2.get('userId')}")
        code1, code2 = d1.get("text", ""), d2.get("text", "")
        if not code1.strip() or not code2.strip():
            print("One or both code snippets are empty, skipping.")
            continue

        ast_s = _ast_similarity(code1, code2)
        tok_s = _token_similarity(code1, code2)
        cfg_s = _cfg_similarity(code1, code2)
        score = _weighted(ast_s, tok_s, cfg_s)

        if score >= threshold:
            match = {
                "source": f'{d1.get("userId", "")}: {d1.get("fileId", "")}',
                "target": f'{d2.get("userId", "")}: {d2.get("fileId", "")}',
                "similarity": round(score, 4)
            }
            print(f"--> Match found: {match}")
            matches.append(match)
        else:
            print("--> No match, below threshold.")

    print(f"\nTotal matches found: {len(matches)}")
    return matches
