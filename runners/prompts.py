# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PROMPTERS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

START_PROMPT = """Please determine the necessary file type, then run all relevant tools to analyze the following code:
```
{func}
```

Only reply with the response from your tool call. Do not include any further information.
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TOOLRAG
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AGENT_PROMPT = ("You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " You are not allowed to return an empty response under any circumstance, instead state DONE."
                " You have access to the following tools: {tool_names}.\n{system_message}"
                )

SAST_SYSTEM_PROMPT = ("You should run all relevent static analysis tools to provide outputs for the Summarizer to use."
                      " If you are done running tools, you must state 'No more applicable tools.'"
                      )

SUMMARIZE_SYSTEM_PROMPT = "You should provide accurate summarizations of previously generated information for all other models to use."

ANALYZE_SYSTEM_PROMPT = ("You should use the provided information to detect all potential vulnerabilties in the originally presented code sample."
                         " You may request additional information. You should avoid false positives and false negatives."
                         )

HUMAN_SAST_SUMMARIZER = ("Please summarize all of the static analysis results from all of the previous tool runs."
                         " Indicate which tools you are summarizing in your response."
                         )

HUMAN_ANALYZER_SUMMARIZER = ("Prepend your response with FINAL ANSWER. Follow this with VULNERABLE or SAFE depending on the results."
                             " Immediately after, include a CONFIDENCE SCORE, with a score describing your certainty regarding"
                             " your analysis on a scale from 0 to 10. Do not base the vulnerable status and confidence on any remediation provided."
                             " Carefully work through the provided information to ensure that your response is accurate. Be certain to distill the most"
                             " recent evaluation from the given information."
                             " Please summarize the following results:"
                             "\n{results}"
                             )

HUMAN_SUMMARIZER_ANALYZER = ("Please utilize the output of the summary to inform your analysis of the original code sample."
                    " Evaluate it for any vulnerabilities you can find while avoiding false positives."
                    " Intensively review all detections, reasoning through to ensure they are accurate."
                    " If no true positive vulnerabilities are found respond NONE in your analysis description."
                    " You have access to a peer RAG agent. If you would like more basic information on a vulnerability,"
                    " then at the end of your response, respond with 'QNA:', then your list of questions. Your questions"
                    " should be at the very end of your message. Keep your questions as simple as possible, as you are"
                    " querying the Common Weakness Enumeration database. An example request would be to provide a" 
                    " description or example of a specific type of vulnerability. When you have exhaustively reasoned through"
                    " all existing vulnerabilities, and excluded all false postives, output your final revised analysis prepended by:"
                    " FINAL ANALYSIS:"
                    )

HUMAN_RAG_ANALYZER = ("The answers to your questions are as follows:\n{results}\n\n"
                      "Please use the above answers to further inform your analysis."
                      " You may ask further questions as needed."
                      " When you have no more questions and have exhaustively reasoned through all existing vulnerabilities "
                      " and excluded all false postives, output your revised final analysis prepended by: FINAL ANALYSIS:"
                      )

HUMAN_RAGLIMIT_ANALYZER = ("The answers to your questions are as follows:\n{results}\n\n"
                      "Please use the above answers to further inform your analysis."
                      " You have reached your question limit, and are not permitted to ask any further questions."
                      " When you have exhaustively reasoned through all existing vulnerabilities,"
                      " and excluded all false postives, output your revised final analysis prepended by: FINAL ANALYSIS:"
                      )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# RAG
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DOC_GRADER_SYSTEM = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

DOC_GRADER_HUMAN = "Retrieved document: \n\n {document} \n\n User question: {question}"

GENERATOR = ("You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question."
             " If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\n"
             "Question: {question}\n"
             "Context: {context}\n"
             "Answer:"
             )

HALLUCINATION_GRADER_SYSTEM = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""

HALLUCINATION_GRADER_HUMAN = "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"

ANSWER_GRADER_SYSTEM = """You are a grader assessing whether an answer addresses / resolves a question \n 
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""

ANSWER_GRADER_HUMAN = "User question: \n\n {question} \n\n LLM generation: {generation}"

REWRITER_SYSTEM = """You a question re-writer that converts an input question to a better version that is optimized \n 
     for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""

REWRITER_HUMAN = "Here is the initial question: \n\n {question} \n Formulate an improved question."