import torch

_model = None
_tokenizer = None

def detect_ai(code: str) -> str:
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        MODEL_NAME = "Salesforce/codet5p-220m-py"
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        _model.eval()  # Puts model in inference mode

    prompt = (
        "Decide whether the following code is likely written by an AI or a human after carefully analyzing it. "
        "Respond only with 'AI' or 'Human'.\n\n"
        f"Code:\n{code}\n\nAnswer:"
    )

    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            max_length=20,
            num_beams=3,
            do_sample=False,
            early_stopping=True
        )

    response = _tokenizer.decode(outputs[0], skip_special_tokens=True).strip().lower()
    return 'ai' in response
