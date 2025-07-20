from flask import Blueprint, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

from similarity_python import python_matches
from java_ast import matches as java_matches
from cpp_ast import matches as cpp_matches
from js_ast import matches as js_matches
from detect_ai import detect_ai

routes = Blueprint("routes", __name__)

EXTS = {
    "python": (".py",),
    "java": (".java",),
    "cpp": (".cpp", ".cc", ".cxx", ".hpp", ".h"),
    "javascript": (".js", ".jsx", ".mjs"),
    "text": tuple(),  # treat every file as “text”
}

ALGOS = {
    "python": python_matches,
    "java": java_matches,
    "cpp": lambda d: cpp_matches(d, threshold=0.6),
    "javascript": js_matches,
}

def normalize(t: str) -> str:
    t = re.sub(r'(?:\s(?=\S))', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.lower().strip()

@routes.route("/detect-ai/batch", methods=["POST"])
def detect_ai_route():
    payload = request.get_json(force=True)
    documents = payload.get("documents", [])

    if not documents or not isinstance(documents, list):
        return jsonify(error="Invalid documents payload"), 400

    try:
        results = []
        for d in documents:
            text = d.get("text", "")
            fileId = d.get("fileId")
            if not fileId or not text:
                continue
            is_ai = detect_ai(text)
            results.append({ "fileId": fileId, "is_ai": is_ai })
        return jsonify(results=results)
    except Exception as e:
        return jsonify(error=f"Batch AI detection failed: {str(e)}"), 500

@routes.route("/internal-plagiarism", methods=["POST"])
def internal_plag():
    payload = request.get_json(force=True)
    lang = payload.get("language")
    docs = payload.get("documents", [])

    if lang not in EXTS:
        return jsonify(error="Unsupported language"), 400
    if len(docs) < 2:
        return jsonify(matches=[], invalid=[])

    want_exts = EXTS[lang]
    valid = []
    invalid = []

    for d in docs:
        filename = d.get("fileName", "").lower()
        if not want_exts or filename.endswith(want_exts):
            valid.append(d)
        else:
            invalid.append(d)

    # If fewer than 2 valid docs, skip matching
    if len(valid) < 2:
        return jsonify(matches=[], invalid=[d["fileName"] for d in invalid])

    # Generic TF-IDF text match
    if lang == "text":
        try:
            ids = [f'{d["userId"]}:{d["fileId"]}' for d in valid]
            vec = TfidfVectorizer(ngram_range=(1, 3), stop_words="english")
            tfidf_matrix = vec.fit_transform([normalize(d["text"]) for d in valid])
            sims = cosine_similarity(tfidf_matrix)
            matches = [
                {
                    "source": ids[i],
                    "target": ids[j],
                    "similarity": round(float(sims[i, j]), 4),
                }
                for i in range(len(ids))
                for j in range(i + 1, len(ids))
                if sims[i, j] >= 0.75
            ]
            return jsonify(matches=matches, invalid=[d["fileName"] for d in invalid])
        except Exception as e:
            return jsonify(error=f"TF-IDF match failed: {str(e)}"), 500

    # AST-based language-specific match
    try:
        matches = ALGOS[lang](valid)
        return jsonify(matches=matches, invalid=[d["fileName"] for d in invalid])
    except Exception as e:
        return jsonify(error=f"{lang} matcher failed: {str(e)}"), 500
