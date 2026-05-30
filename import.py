from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "./models/mistral-7b",
    device_map="auto",
    load_in_4bit=True
)