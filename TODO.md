# TODO for ToolRAG

### Todo

- [ ] Investigate human feedback node
- [ ] Will getting last SAST message include all tool responses?
- [ ] Maybe I should re-send the original code snippet to the analyzer directly?
- [ ] Check output of multiple tools
- [ ] Should I have final output indicate tools used, and if RAG used?
- [ ] If so, should that be handled by LLM or later parser?
- [ ] NOTE: Run 6 worked pretty good
- [ ] Confirm summarizer actually SUMMARIZES tool outputs
- [ ] What things should I pass directly, versus instruct/provide using state history context?
- [ ] Should different RAG steps use different models?
- [ ] Docker pre-check script to avoid mount directory already exists error