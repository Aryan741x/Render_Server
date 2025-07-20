import platform
import subprocess
import os
from difflib import SequenceMatcher
from itertools import combinations
import platform

if platform.system() == "Windows":
    CTAGS_EXE = os.environ.get("CTAGS_PATH", "bin/ctags.exe")  # relative fallback
else:
    CTAGS_EXE = "ctags"

def extract_tokens(code: str) -> list[str]:
    with open("temp.cpp", "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run([
            CTAGS_EXE, "-x", "--c++-kinds=+p", "--fields=+n", "--language-force=C++", "temp.cpp"
        ], capture_output=True, text=True, check=True)

        lines = result.stdout.strip().split("\n")
        tokens = [line.split()[0] for line in lines if line.strip()]
        return tokens

    except Exception as e:
        print(f"[ctags] Error: {e}")
        return []

def _sim(a: str, b: str) -> float:
    t1, t2 = extract_tokens(a), extract_tokens(b)
    return SequenceMatcher(None, t1, t2).ratio() if t1 and t2 else 0.0

def matches(docs, threshold=0.6):
    out = []
    for d1, d2 in combinations(docs, 2):
        score = _sim(d1["text"], d2["text"])
        if score >= threshold:
            out.append({
                "source": d1["fileName"],
                "target": d2["fileName"],
                "similarity": round(score, 4)
            })
    return out
