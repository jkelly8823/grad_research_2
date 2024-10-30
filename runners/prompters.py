import json
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()

# Custom
from parsers import *
from prompts import *

# !!!!!!!!!!!!!!!!!!!!!!!!!!
# MOSTLY COPIED FROM PRIMEVUL. NEED TO EDIT
# !!!!!!!!!!!!!!!!!!!!!!!!!!
# How do I want to handle message truncation? Should I allow, or pass over?
def truncate_tokens_from_messages(conversations, model, max_gen_length):
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

    trunc_convos = []
    for messages in conversations:
        num_tokens = 3  # every reply is primed with <|start|>assistant<|message|>
        trunc_messages = []
        for message in messages:
            num_tokens += tokens_per_message
            tm = ()
            for val in message:
                encoded_value = encoding.encode(val)
                num_tokens += len(encoded_value)
                if num_tokens > max_tokens:
                    print(f"Truncating message: {val[:100]}...")
                    tm += (encoding.decode(encoded_value[:max_tokens - num_tokens]),)
                    break
                else:
                    tm += (val,)
            trunc_messages.append(tm)
        trunc_convos.append(trunc_messages)
    return trunc_convos

# !!!!!!!!!!!!!!!!!!!!!!!!!!
# My Work
# !!!!!!!!!!!!!!!!!!!!!!!!!!
def form_prompts(src, prompt, limit=-1):
    prompts = []
    sys = ("system", SYS_INST)
    if src == 'BRYSON':
        samples = get_bryson_data(os.getenv('bryson'), limit)
    elif src == 'PRIMEVUL':
        samples = get_primevul_data(os.getenv('primevul'), limit)
    for sample in samples:
        sample['prompt'] = prompt.format(func = sample['func'])
        prompts.append([sys, ("human", sample['prompt'])])
    return [samples, prompts]