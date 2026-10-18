---
name: empirical-did-replication
description: Reconstruct two-wave DID results and generate the final report, tables and figures.
---

# Reusable empirical workflow

1. Read the paper, course targets and data dictionary; identify the estimand,
   treatment/comparison groups, outcome, sample exclusions and extension.
2. Put authorized unmodified course inputs in data/raw/01_DID/ and the author
   archive in data/raw/author/njmin_author.zip. Check provenance and file hashes.
3. Install code/requirements.txt and run python code/run_all.py.
4. Check composite identifiers, missing observations, permanent/temporary
   closures, sample counts and variable definitions before interpreting models.
5. Compare Table 2-4 outputs with the paper; retain unresolved source differences.
   Review the required wage figure and ownership extension with uncertainty.
6. Use algebra, independent OLS, accounting identities and unit tests. Repeat
   execution with the same seed to check deterministic final outputs.
7. Keep only the formal report, required disclosure, final data, code and one
   format per result. Intermediates stay in the automatically deleted run folder.
8. Explain identification limits, AI use and actual corrections. With one
   pre-policy wave, do not invent a pre-trend test. Keep restricted data private.

Entry point: code/run_all.py. Dependencies and supporting modules are in code/.
Deliverables map one-to-one to the required structure in README.md.
