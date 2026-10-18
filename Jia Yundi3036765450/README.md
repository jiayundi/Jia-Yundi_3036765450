# ECON6067 individual project: Card and Krueger (1994)

## Submission structure

This folder follows the course submission table. There is one formal report,
one AI disclosure and one reproducible workflow. Outputs are supplied once:
tables as CSV, figures as PNG. No HTML, duplicate copies, separate PDF figures,
logs, old report versions or intermediate work files are submitted.

| Required item | Submitted path |
|---|---|
| Reproduction instructions | README.md |
| Final research report | report.pdf |
| AI use: applications, checking, corrections | AI_USE_DISCLOSURE.md |
| Raw inputs | data/raw/01_DID/ and data/raw/author/njmin_author.zip |
| Final analysis datasets | data/processed/analysis_store.csv; analysis_panel.csv |
| Single execution entry point | code/run_all.py |
| Other necessary code | code/analysis.py; figures.py; report.py; test_replication.py |
| Dependencies | code/requirements.txt |
| Generated tables | outputs/tables/ (9 CSV files) |
| Generated figures | outputs/figures/ (6 PNG files) |
| Generated figure data | outputs/data/figure1_bins.csv |
| Reusable skill | skills/SKILL.md |

The Chinese labels in the course table correspond to data/raw, data/processed,
outputs/tables, outputs/figures, outputs/data and skills. The original numbered
01_DID folder and its filenames are preserved. Supporting code is all in code/.

## Run all results

Python 3.12 is recommended. From this folder:

```bash
python -m pip install -r code/requirements.txt
python code/run_all.py
```

All required raw inputs are included for authorized course use. No manual edits
are needed. The command reconstructs variables, estimates all models, runs
21 analytical checks and 6 unit tests, and rebuilds the report and final outputs.
It resolves paths from the script location and can be invoked by absolute path
from another working directory. Temporary files and font caches are removed
automatically; the command does not generate HTML or extra report copies.

The workflow uses seed 6067 and 4,999 bootstrap repetitions. Optional arguments:
`--input PATH` for another authorized course CSV and `--bootstrap NUMBER`.
The small author archive is bundled. If missing it is fetched from the documented
public URL, with its SHA-256 checked before use; network access is then required.

## Data sources and access

Course data: 01_DID/data/public.csv, 410 restaurants and 46 variables.
SHA-256: 45e6f4ac4928f7c9fcc2585a45e0467ecaa039f0b241f4c5a26cd290fd8e772b.

Independently retrieved author source, 16 October 2026:
https://davidcard.berkeley.edu/data_sets.html
https://davidcard.berkeley.edu/data_sets/njmin.zip
SHA-256: 41a29aec6b489658b20030d044a2b20a5f5a04b871cde41df057afd6013ba587.
public.dat matches all 18,860 course CSV cells, including missingness. This is
the same original survey, not an expanded sample. The archive also includes
the codebook and author SAS program used for auditing definitions and models.

The store dataset has constructed FTE, wage gap and sample flags. The panel
dataset has both waves, store identifiers and the NJ x Post interaction.
STATE plus SHEET identifies stores. Missing employee components remain missing;
permanent closures have zero post-employment, temporary closures remain missing
in the baseline. The balanced sample is 384 and wage-complete sample 357.

This complete folder contains restricted course and restaurant-level data.
Keep the GitHub repository PRIVATE and grant access to the teaching team.
Do not publish these data or course download links. All phased development
history remains in the hidden .git directory; push that history rather than
starting from a single file upload. No remote or submission is configured.

## Final table files and limitations

table2.csv, table3.csv and table4.csv include original comparisons. Other files
contain ownership heterogeneity, robustness, regional specification audit,
employment components, uncertainty comparisons and chain-exclusion sensitivity.
Intermediate descriptive/missingness tables are used internally where needed,
not submitted as additional files. The report contains the full discussion.

Some Table 3 standard errors and the 85.5% versus 85.2% wage-share discrepancy
remain unreconciled. Regional ownership controls differ between author code and
paper labels; both specifications are retained. Historical Figure 1 bin edges
cannot be fully verified. One pre-period cannot establish parallel trends;
ownership interactions do not prove a mechanism. See report.pdf for details.
