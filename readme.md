How to Use This Tool
Step 1: Install pycparser
bashpip install pycparser
Step 2: Run on Single File
bashpython move_analyzer.py source_code/process_a.c
Step 3: Run on Directory
bashpython move_analyzer.py source_code/
```

### Step 4: View Results
```
analysis_output/
├── process_a.c_analysis.md      # Markdown report
├── process_a.c_callgraph.dot    # Graphviz call graph
├── process_b.c_analysis.md
├── process_b.c_callgraph.dot
├── all_move_operations.json     # Combined MOVE operations
└── all_call_graphs.json         # Combined call graphs
Step 5: Generate Diagram Images
bashdot -Tpng analysis_output/process_a.c_callgraph.dot -o callgraph.png
```

---
