# evaluation/

Required reports, bundled into `code.zip`:

- `evaluation_report.md`: case-level status accuracy, step- and field-level accuracy, sequence accuracy, 5 participant-made cases, and the failures found and improvements made, with scores after each change.
- `usage_report.md`: providers and models, call counts, input/output tokens, total and per-request tokens, and cost for the run that produced `output.csv`.

To reproduce the numbers:

```bash
python3 code/main.py --split sample && python3 code/tests/evaluate.py
python3 code/tests/custom_cases.py
```
