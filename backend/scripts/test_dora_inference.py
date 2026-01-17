#!/usr/bin/env python3
"""Test inference on DoRA-trained Elson 14B model"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

def load_model():
    print("Loading base model...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )

    base_path = os.path.expanduser("~/base_model/final")
    adapter_path = os.path.expanduser("~/wealth-dora-elson14b")

    tokenizer = AutoTokenizer.from_pretrained(base_path, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        base_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    print("Loading DoRA adapter...")
    model = PeftModel.from_pretrained(model, adapter_path)

    return model, tokenizer

def generate_response(model, tokenizer, question, max_new_tokens=512):
    prompt = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    # Extract assistant response
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]
        if "<|im_end|>" in response:
            response = response.split("<|im_end|}")[0]

    return response.strip()

def main():
    model, tokenizer = load_model()

    test_questions = [
        "How should I allocate my 401k investments at age 35?",
        "What's the best strategy for saving for my child's college education?",
        "How do I minimize taxes on my investment gains?",
        "I have $100,000 to invest. Should I pay off my mortgage or invest in the market?",
        "What estate planning steps should I take to protect my family's wealth?",
    ]

    print("\n" + "="*70)
    print("DoRA Model Inference Test - Elson 14B Wealth Management")
    print("="*70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}: {question}")
        print("-"*70)

        response = generate_response(model, tokenizer, question)
        print(f"Response:\n{response}")

    print("\n" + "="*70)
    print("Inference test complete!")
    print("="*70)

if __name__ == "__main__":
    main()
