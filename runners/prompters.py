from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Custom
from dataset_parsers import *
from prompts import *

def form_prompts(src, prompt, limit=-1, cherrypick = []):
    convos = []
    if src == 'BRYSON':
        samples = get_bryson_data(os.getenv('bryson'), limit, cherrypick)
    elif src == 'PRIMEVUL':
        samples = get_primevul_data(os.getenv('primevul'), limit, cherrypick)
    for sample in samples:
        sample['prompt'] = prompt.format(func = sample['func'])
        convos.append([HumanMessage(sample['prompt'])])
    return [samples, convos]


# samples, convos = form_prompts('PRIMEVUL',SAST_PROMPT, 2)
# with open("msg1-1.txt", "w+", encoding="utf-8", errors="replace") as f:
#     for convo in convos:
#         for c in convo:
#             f.write(str(c))
#             f.write('\n\n' + '~'*100 + '\n\n')
#         f.write('\n\n' + '='*100 + '\n' + '='*100 + '\n'*4)