# TODO for ToolRAG

### Todo

- [X] Investigate human feedback node
- [X] Will getting last SAST message include all tool responses?
- [X] Check output of multiple tools
- [X] Confirm summarizer actually SUMMARIZES tool outputs
- [ ] What things should I pass directly, versus instruct/provide using state history context?
    - [ ] Maybe I should re-send the original code snippet to the analyzer directly?
        - [ ] If so, should that be handled by LLM or later parser?
- [ ] Should I have final summarized output indicate tools used, and if RAG used?
- [ ] Should different RAG steps use different models?
- [ ] Docker pre-check script to avoid mount directory already exists error
- [ ] How to improve RAG retrieval?
    - [ ] It fails on "What is CWE-288?"
    - [ ] MMR vs standard similarity for retrieval?
- [ ] Move all prompts to prompts.py
- [ ] Fix token limits in prompters.py
    - [ ] Add MAX_GEN_LENGTH to env file instead
    - [ ] Change how model name get passed to truncater func
- [ ] Tweak analyzer prompt to avoid grading remediated code, and focus on the original sourcecode
- [ ] Correct parsed writer, some return lists in content?