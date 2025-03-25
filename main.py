from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

model_name = "meta-llama/Llama-3.2-3B-Instruct" 
tokenizer = AutoTokenizer.from_pretrained(model_name)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, 
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config, device_map="auto")

input_text = "capital of france"

# Encode input properly
input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to("cuda")

# Generate output
with torch.no_grad():
    output_ids = model.generate(input_ids, max_new_tokens=100)

# Decode output correctly
decoded_output = tokenizer.decode(output_ids[0], skip_special_tokens=True)
print(decoded_output)