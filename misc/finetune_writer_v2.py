import json
import re
import pandas as pd
import math
import random

ANALYZE_SYSTEM_PROMPT = (" You are an expert in the fields of cybersecurity and code analysis."
                         " You should use the provided information to detect all potential vulnerabilties in the originally presented code sample."
                        #  " You may request additional information."
                         " You should avoid false positives and false negatives."
                         )

HUMAN_SUMMARIZER_ANALYZER = ("Please utilize the output of the summary to inform your analysis of the original code sample."
                    " Evaluate it for any vulnerabilities you can find while avoiding false positives."
                    " Intensively review all detections, reasoning through to ensure they are accurate."
                    " Utilize the tool summaries to assist your analysis, but do not solely rely upon them."
                    " Perform an additional step-by-step intense evaluation of code using your capabilities."
                    " If no true positive vulnerabilities are found respond NONE in your analysis description."
                    # " You have access to a peer RAG agent. If you would like more basic information on a vulnerability,"
                    # " then at the end of your response, respond with 'QNA:', then your list of questions. Your questions"
                    # " should be at the very end of your message. Keep your questions as simple as possible, as you are"
                    # " querying the Common Weakness Enumeration database. An example request would be to provide a" 
                    # " description or example of a specific type of vulnerability. If you have no questions,"
                    # " end your response with 'END' instead. Please engage in at least one round of QNA. "
                    " When you have exhaustively reasoned through all existing vulnerabilities, and excluded all false postives,"
                    " output your final revised analysis prepended by: 'FINAL ANALYSIS:'."
                    " Include a line stating 'VERDICT:', then 'VULNERABLE' or 'SAFE' based upon your results."
                    )

# Read the CSV file to filter relevant rows
verdicts = pd.read_csv(r'D:\grad_research_2\outputs\prev\bulk_run_1\verdicts.csv')
verdicts = verdicts[verdicts['true_vuln'] == verdicts['predicted_vuln']]

fine_lines = []
# Iterate over each row in the filtered DataFrame
for idx, row in verdicts.iterrows():
    # Open the corresponding log file and process the first line
    with open(rf'D:\grad_research_2\outputs\prev\filtered_bulk_run\parsed\run_{row["run"]}_parsed.txt', 'r') as log:
        lines = log.read()

        input_mark = ("--------------------------------------------------\n"
                    "Input\n"
                    "--------------------------------------------------\n"
        )
        summarizer_mark = ("--------------------------------------------------\n"
                    "Summarizer\n"
                    "--------------------------------------------------\n"
        )
        analyzer_mark = ("--------------------------------------------------\n"
                    "Analyzer\n"
                    "--------------------------------------------------\n"
        )
        stop_str = "--------------------------------------------------\n"
        
        input_loc = lines.find(input_mark) + len(input_mark)
        input_loc2 = lines.find(stop_str,input_loc)
        input_lines = lines[input_loc:input_loc2].strip()

        # print(input_lines)

        summarize_loc = lines.find(summarizer_mark) + len(summarizer_mark)
        summarize_loc2 = lines.find(stop_str,summarize_loc)
        summarizer_lines = lines[summarize_loc:summarize_loc2].strip()

        # print(summarizer_lines)

        analyze_loc = lines.rfind(analyzer_mark) + len(analyzer_mark)
        analyze_loc2 = lines.find(stop_str,analyze_loc)
        analyzer_lines = lines[analyze_loc:analyze_loc2].strip()

        # print(analyzer_lines)
            
        line = {"messages":
            [
                {"role": "system", "content": ANALYZE_SYSTEM_PROMPT.strip()},
                {"role": "user", "content": input_lines},
                {"role": "assistant", "content": summarizer_lines, "weight":0},
                {"role": "user", "content": HUMAN_SUMMARIZER_ANALYZER.strip()},
                {"role": "assistant", "content": analyzer_lines, "weight":1}
            ]
        }

        fine_lines.append(line)

random.shuffle(fine_lines)

finetune = open(r'D:\grad_research_2\datasets\finetunes_train_primevul_v2.jsonl', 'w+')
validation = open(r'D:\grad_research_2\datasets\finetunes_validate_primevul_v2.jsonl', 'w+')
split = math.ceil(0.8 * len(fine_lines))

for idx, line in enumerate(fine_lines):
    if idx <= split:
        finetune.write(json.dumps(line) + "\n")
    else:
        validation.write(json.dumps(line) + "\n")
finetune.close()
validation.close()