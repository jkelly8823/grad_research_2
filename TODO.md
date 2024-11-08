# TODO for ToolRAG

### Todo

- [X] Investigate human feedback node
- [X] Will getting last SAST message include all tool responses?
- [X] Check output of multiple tools
- [X] Confirm summarizer actually SUMMARIZES tool outputs
- [ ] Maybe I should re-send the original code snippet to the analyzer directly?
- [ ] If so, should that be handled by LLM or later parser?
- [ ] Should I have final output indicate tools used, and if RAG used?
- [ ] What things should I pass directly, versus instruct/provide using state history context?
- [ ] Should different RAG steps use different models?
- [ ] Docker pre-check script to avoid mount directory already exists error
- [ ] How to improve RAG retrieval?
    - [ ] It fails on "What is CWE-288?"
    - [ ] MMR vs standard similarity for retrieval?