from langchain_core.messages import HumanMessage, SystemMessage
import json
import tiktoken
import os
from dotenv import load_dotenv

load_dotenv()

# Custom
from dataset_parsers import *
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
        # print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    

    trunc_convos = []
    for message in conversations:
        trunc_messages = []
        encoded_value = encoding.encode(message)
        num_tokens = len(encoded_value)
        if num_tokens > max_tokens:
            print(f"Truncating message: {message[:50]}...")
            chunk_size = max_tokens-20
            chunks = [encoding.decode(encoded_value[i:i + chunk_size]) for i in range(0, len(encoded_value), chunk_size)]
            chunk_len = len(chunks)
            trunc_messages.append(HumanMessage(f"Due to size of the input, I will be sending the input across {chunk_len} messages. Please wait to recieve all before continuing. Please indicate once you have recieved the entire code block."))
            for i in range(0, chunk_len):
                trunc_messages.append(HumanMessage(f"MESSAGE {i+1}/{chunk_len}:\n" + chunks[i]))
        else:
            trunc_messages.append(HumanMessage(message))
        trunc_convos.append(trunc_messages)
    return trunc_convos

# !!!!!!!!!!!!!!!!!!!!!!!!!!
# My Work
# !!!!!!!!!!!!!!!!!!!!!!!!!!
def form_prompts(src, prompt, limit=-1):
    prompts = []
    if src == 'BRYSON':
        samples = get_bryson_data(os.getenv('bryson'), limit)
    elif src == 'PRIMEVUL':
        samples = get_primevul_data(os.getenv('primevul'), limit)
    for sample in samples:
        sample['prompt'] = prompt.format(func = sample['func'])
        prompts.append(sample['prompt'])
    return [samples, prompts]


samples, convos = form_prompts('PRIMEVUL',SAST_PROMPT, 2)
convos = truncate_tokens_from_messages(convos, "claude-3-haiku-20240307", 2048)
with open("msg1-1.txt", "w+", encoding="utf-8", errors="replace") as f:
    for convo in convos:
        for c in convo:
            f.write(str(c))
            f.write('\n\n' + '~'*100 + '\n\n')
        f.write('\n\n' + '='*100 + '\n' + '='*100 + '\n'*4)