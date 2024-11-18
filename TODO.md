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
- [ ] Docker pre-check script to avoid mount directory already exists error
- [ ] How to improve RAG retrieval?
    - [ ] It fails on "What is CWE-288?"
    - [ ] MMR vs standard similarity for retrieval?
    - [X] Add document fields
- [X] Move all prompts to prompts.py
- [X] Fix token limits in prompters.py
    - [X] Add MAX_INPUT_LENGTH to env file instead
    - [X] Doc said ignore stupidly long files
- [ ] Tweak analyzer prompt to avoid grading remediated code, and focus on the original sourcecode
- [ ] Write methods section by mid next week
- [ ] Get data flow finalized by Thurs
- [ ] Finish all data runs by middle of next week
- [ ] Set limit on number of RAG calls

- [ ] Fix counts and rate of outcomes, seems fishy
- [ ] WHY THE OUTCOMES PAIR SO FEW? ONLY 19 vs 124 total samples????
- [X] Fix classification counts by CWE
- [X] Add classification rates by CWE
- [X] Maybe redo rates? Out of total samples probably isn't best metric...
- [ ] WTH is with the tabs in sample 195801
