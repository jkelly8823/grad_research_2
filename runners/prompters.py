# !!!!!!!!!!!!!!!!!!!!!!!!!!
# COPIED FROM PRIMEVUL. NEED TO EDIT
# !!!!!!!!!!!!!!!!!!!!!!!!!!
import json
import tiktoken

def truncate_tokens_from_messages(messages, model, max_gen_length):
    """
    Count the number of tokens used by a list of messages, 
    and truncate the messages if the number of tokens exceeds the limit.
    Reference: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    """

    if model == "gpt-3.5-turbo-0125":
        max_tokens = 16385 - max_gen_length
    elif model == "gpt-4-0125-preview":
        max_tokens = 128000 - max_gen_length
    else:
        max_tokens = 4096 - max_gen_length
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3

    num_tokens = 3  # every reply is primed with <|start|>assistant<|message|>
    trunc_messages = []
    for message in messages:
        tm = {}
        num_tokens += tokens_per_message
        for key, value in message.items():
            encoded_value = encoding.encode(value)
            num_tokens += len(encoded_value)
            if num_tokens > max_tokens:
                print(f"Truncating message: {value[:100]}...")
                tm[key] = encoding.decode(encoded_value[:max_tokens - num_tokens])
                break
            else:
                tm[key] = value
        trunc_messages.append(tm)
    return trunc_messages


def construct_prompts(input_file, inst):
    with open(input_file, "r") as f:
        samples = f.readlines()
    samples = [json.loads(sample) for sample in samples]
    prompts = []
    for sample in samples:
        key = sample["project"] + "_" + sample["commit_id"]
        p = {"sample_key": key}
        p["func"] = sample["func"]
        p["target"] = sample["target"]
        p["prompt"] = inst.format(func=sample["func"])
        prompts.append(p)
        break
    return prompts

# print(construct_prompts(r'D:\grad_research_2\datasets\PrimeVul\primevul_test_paired.jsonl',PROMPT_INST))