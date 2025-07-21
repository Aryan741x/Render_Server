from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load the model once globally
MODEL_NAME = "Salesforce/codet5p-220m-py"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
model.eval()

def detect_ai(code: str) -> str:
    prompt = (
        "Decide whether the following code is likely written by an AI or a human after carefully analyzing it. "
        "Respond only with 'AI' or 'Human'.\n\n"
        f"Code:\n{code}\n\nAnswer:"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=20,
            num_beams=3,
            do_sample=False,
            early_stopping=True
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip().lower()

    return 'ai' in response
    
  
