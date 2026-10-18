"""One-command reproduction; intermediate files are automatically discarded."""
from pathlib import Path
import argparse
import contextlib
import hashlib
import io
import os
import shutil
import sys
import tempfile
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
AUTHOR_URL = 'https://davidcard.berkeley.edu/data_sets/njmin.zip'
AUTHOR_SHA = '41a29aec6b489658b20030d044a2b20a5f5a04b871cde41df057afd6013ba587'
TABLES = {
    'table2.csv': 'table2_replication.csv',
    'table3.csv': 'table3_comparison.csv',
    'table4.csv': 'table4_comparison.csv',
    'ownership_extension.csv': 'ownership_extension.csv',
    'robustness.csv': 'robustness.csv',
    'regional_specification_audit.csv': 'regional_specification_audit.csv',
    'employment_components.csv': 'employment_components.csv',
    'inference_comparison.csv': 'inference_comparison.csv',
    'leave_one_chain_out.csv': 'leave_one_chain_out.csv',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=ROOT/'data/raw/01_DID/data/public.csv')
    parser.add_argument('--bootstrap',type=int,default=4999)
    args = parser.parse_args()
    if args.bootstrap < 2:
        parser.error('--bootstrap must be at least 2')
    if not args.input.is_file():
        parser.error('Place authorized 01_DID/data/public.csv under data/raw/, or use --input.')
    archive = ROOT/'data/raw/author/njmin_author.zip'
    if not archive.exists():
        archive.parent.mkdir(parents=True,exist_ok=True)
        request=urllib.request.Request(AUTHOR_URL,headers={'User-Agent':'ECON6067-Replication/1.0'})
        with urllib.request.urlopen(request,timeout=60) as response:
            content=response.read()
        if hashlib.sha256(content).hexdigest()!=AUTHOR_SHA:
            raise ValueError('Author archive changed; review the new source before using it.')
        archive.write_bytes(content)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=AUTHOR_SHA:
        raise ValueError('Unexpected author-archive SHA-256')
    # All estimation intermediates, diagnostic files and font caches stay here.
    # TemporaryDirectory removes them even if an exception is raised.
    with tempfile.TemporaryDirectory(prefix='.run_',dir=ROOT) as temporary:
        work=Path(temporary)
        for folder in ['data/processed','input/external','outputs/tables','outputs/figures','outputs/logs','tmp']:
            (work/folder).mkdir(parents=True,exist_ok=True)
        os.environ['MPLCONFIGDIR']=str(work/'tmp/matplotlib')
        shutil.copy2(archive,work/'input/external/njmin_author.zip')
        from analysis import main as analyze
        from figures import main as draw
        from report import main as report
        import test_replication
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):
            data,results=analyze(work,args.input,args.bootstrap)
            draw(work,data)
            tests=unittest.defaultTestLoader.loadTestsFromModule(test_replication)
            checked=unittest.TextTestRunner(stream=capture,verbosity=2).run(tests)
            if not checked.wasSuccessful():
                raise RuntimeError(capture.getvalue())
            report(work)
        # Publish only the final files listed in the submission README.
        for folder in ['outputs/tables','outputs/figures','outputs/data','data/processed']:
            (ROOT/folder).mkdir(parents=True,exist_ok=True)
        for target,source in TABLES.items():
            shutil.copy2(work/'outputs/tables'/source,ROOT/'outputs/tables'/target)
        for figure in (work/'outputs/figures').glob('*.png'):
            shutil.copy2(figure,ROOT/'outputs/figures'/figure.name)
        for name in ['analysis_store.csv','analysis_panel.csv']:
            shutil.copy2(work/'data/processed'/name,ROOT/'data/processed'/name)
        shutil.copy2(work/'outputs/tables/figure1_original_bins.csv',ROOT/'outputs/data/figure1_bins.csv')
        shutil.copy2(work/'report.pdf',ROOT/'report.pdf')
    print('Completed: report.pdf; 9 final CSV tables; 6 PNG figures; 2 analysis datasets; 1 figure dataset.')
    print('Passed: 21 analytical checks and 6 unit tests. Temporary files removed.')

if __name__ == '__main__':
    main()
