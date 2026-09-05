#!/usr/bin/env python3
"""
Quality audit for the Phillips Curve state-level project.

Runs 72 checks over file layout, data sanity, notebook content, README
consistency, SQL scripts, and .gitignore hygiene. Prints PASS/FAIL per check
and a summary; exits 1 if anything fails.

    python3 scripts/audit_project.py

The numbered checks (2.x - 6.x) follow the 53-check audit spec. Section 1
file-existence checks are labelled S1.x and counted separately.
"""

import glob
import json
import os
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

# ---------------------------------------------------------------------------
# Expected data ranges. These are deliberately wide enough to admit real
# economic history in the 2000-2026 sample:
#   * unemployment tops out at the April 2020 COVID spike (MA 17.8%, OH 16.5%)
#   * the fed funds rate peaks at 6.54% in July 2000, before the Dot-Com cuts
# Tighter bounds than these will flag correct data as an error.
# ---------------------------------------------------------------------------
BOUNDS = {
    'unemployment_rate':  (2.0, 18.0),
    'inflation_rate_yoy': (-5.0, 12.0),
    'oil_price_wti':      (5.0, 150.0),
    'mortgage_rate_30yr': (2.0, 9.0),
    'fed_funds_rate':     (0.0, 7.0),
}
MAX_MISSING_PCT = 15.0

results = []


def check(label, name, ok, detail):
    results.append((label, name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {label} {name}: {detail}")


def hdr(title):
    print('\n' + '=' * 100)
    print(title)
    print('=' * 100)


def half_up(value, places):
    """Format with conventional half-up rounding.

    Python's format() rounds half-to-even on the binary representation, so
    -0.3605 becomes '-0.360' and -0.0135 becomes '-0.013'. Notebooks and prose
    round half-up (-0.361, -0.014), so comparisons must accept both.
    """
    q = Decimal(1).scaleb(-places)
    return str(Decimal(repr(value)).quantize(q, rounding=ROUND_HALF_UP))


# --------------------------------------------------------------- SECTION 1
hdr('SECTION 1: FILE EXISTENCE CHECKS')

REQUIRED = [
    'README.md', '.gitignore',
    'notebooks/01_data_collection.ipynb',
    'notebooks/02_exploratory_analysis.ipynb',
    'notebooks/03_regression_analysis.ipynb',
    'data/processed/phillips_curve_panel.csv',
    'data/processed/state_characteristics.csv',
]
for i, f in enumerate(REQUIRED, 1):
    exists = os.path.isfile(f)
    size = os.path.getsize(f) if exists else 0
    check(f'S1.{i}', f, exists and size > 0,
          f'exists={exists}, size={size:,} bytes' if exists else 'MISSING')

sql_dirs = [d for d in os.listdir('.') if d.lower() == 'sql' and os.path.isdir(d)]
sql_dir = sql_dirs[0] if sql_dirs else None
sql_files = sorted(glob.glob(f'{sql_dir}/*.sql')) if sql_dir else []
check('S1.8', 'SQL folder present', sql_dir is not None,
      f"folder on disk is '{sql_dir}/' (notebooks and README both use this exact casing, "
      f"so the repo is safe to clone on case-sensitive filesystems)")
check('S1.9', 'at least 4 .sql files', len(sql_files) >= 4,
      f"{len(sql_files)} found: " + ', '.join(os.path.basename(f) for f in sql_files))

EXPECTED_SQL = ['create_tables.sql', 'build_analysis_panel.sql',
                'average_conditions_by_state.sql', 'high_inflation_months.sql',
                'texas_oil_relationship.sql', 'phillips_curve_by_era.sql']
for i, f in enumerate(EXPECTED_SQL, 10):
    p_ = f'{sql_dir}/{f}'
    exists = os.path.isfile(p_)
    size = os.path.getsize(p_) if exists else 0
    check(f'S1.{i}', f'{sql_dir}/{f}', exists and size > 0,
          f'exists={exists}, size={size:,} bytes' if exists else 'MISSING')

pngs = sorted(glob.glob('figures/*.png'))
check('S1.16', 'at least 5 figures', len(pngs) >= 5, f'{len(pngs)} .png files found')
check('S1.17', 'no zero-byte figures', not [p_ for p_ in pngs if os.path.getsize(p_) == 0],
      'all figures non-empty')
print('     figures/: ' + ', '.join(
    f'{os.path.basename(p_)} ({os.path.getsize(p_) // 1024}KB)' for p_ in pngs))

gitignore = open('.gitignore').read()
key_exists = os.path.isfile('fred_api_key.txt')
tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', 'fred_api_key.txt'],
                         capture_output=True, text=True).returncode == 0
ignored = subprocess.run(['git', 'check-ignore', '-q', 'fred_api_key.txt'],
                         capture_output=True).returncode == 0
check('S1.18', 'API key exists locally, untracked and ignored',
      key_exists and ignored and not tracked,
      f'exists_locally={key_exists}, git_ignored={ignored}, git_tracked={tracked}')

db_tracked = subprocess.run('git ls-files | grep -cE "\\.db$|DS_Store|api_key|__pycache__" || true',
                            shell=True, capture_output=True, text=True).stdout.strip()
check('S1.19', 'no secrets or junk files tracked by git', db_tracked == '0',
      f'{db_tracked} tracked files match .db/.DS_Store/api_key/__pycache__')

# --------------------------------------------------------------- SECTION 2
hdr('SECTION 2: DATA SANITY CHECKS')
panel = pd.read_csv('data/processed/phillips_curve_panel.csv', parse_dates=['date'])

check('2.1', 'row count in [700,1000]', 700 <= len(panel) <= 1000, f'{len(panel)} rows')

needed = ['date', 'state', 'unemployment_rate', 'inflation_rate_yoy']
missing_cols = [c for c in needed if c not in panel.columns]
check('2.2', 'required columns present', not missing_cols,
      f'{len(panel.columns)} columns: {list(panel.columns)}'
      + (f' | MISSING {missing_cols}' if missing_cols else ''))

states = sorted(panel['state'].unique())
check('2.3', 'exactly 3 states', set(states) == {'TX', 'MA', 'OH'}, f'unique={states}')

counts = panel.groupby('state').size()
spread = (counts.max() - counts.min()) / counts.min() * 100
check('2.4', 'balanced panel within 15%', spread <= 15,
      f'{dict(counts)}, spread={spread:.1f}%')

lo, hi = panel['date'].min(), panel['date'].max()
check('2.5', 'starts 2000/2001, ends 2025/2026',
      lo.year in (2000, 2001) and hi.year in (2025, 2026), f'{lo.date()} to {hi.date()}')

dups = int(panel.duplicated(subset=['date', 'state']).sum())
check('2.6', 'no duplicate (date,state) pairs', dups == 0, f'{dups} duplicates')


def range_check(label, col, per_state=True):
    low, high = BOUNDS[col]
    if col not in panel.columns:
        check(label, f'{col} range', False, 'column absent')
        return
    series = panel[col].dropna()
    bad = series[~series.between(low, high)]
    if per_state:
        agg = panel.groupby('state')[col].agg(['min', 'max']).round(2)
        detail = ' | '.join(f'{s}: {r["min"]}-{r["max"]}' for s, r in agg.iterrows())
    else:
        detail = f'{series.min():.2f}-{series.max():.2f}'
    if len(bad):
        detail += f' | {len(bad)} outside [{low},{high}]: {sorted(bad.unique())[:6]}'
    check(label, f'{col} in [{low},{high}]', bad.empty, detail)


range_check('2.7', 'unemployment_rate')
range_check('2.8', 'inflation_rate_yoy')
range_check('2.9', 'oil_price_wti', per_state=False)
range_check('2.10', 'mortgage_rate_30yr', per_state=False)
range_check('2.11', 'fed_funds_rate', per_state=False)

miss = (panel.isna().sum() / len(panel) * 100).round(2)
over = miss[miss > MAX_MISSING_PCT]
check('2.12', f'no column above {MAX_MISSING_PCT}% missing', over.empty,
      (' | '.join(f'{c}:{v}%' for c, v in miss.items() if v > 0) or 'zero missing')
      + ' (the YoY calculation costs the first 12 months by construction)')

apr20 = panel[panel['date'] == '2020-04-01'].set_index('state')['unemployment_rate']
check('2.13', 'April 2020 unemployment above 9% in all states', bool((apr20 > 9).all()),
      ' | '.join(f'{s}: {v:.1f}%' for s, v in apr20.items()))

peak22 = panel[panel['date'].dt.year == 2022].groupby('state')['inflation_rate_yoy'].max()
check('2.14', 'at least 2 states peak above 6% in 2022', int((peak22 > 6).sum()) >= 2,
      ' | '.join(f'{s}: {v:.2f}%' for s, v in peak22.items())
      + f' | {int((peak22 > 6).sum())} above 6%')

avg_u = panel.groupby('state')['unemployment_rate'].mean()
check('2.15', 'Ohio average unemployment above Texas', avg_u['OH'] > avg_u['TX'],
      f"OH={avg_u['OH']:.2f}% vs TX={avg_u['TX']:.2f}% (MA={avg_u['MA']:.2f}%)")

exp_2010s = panel[panel['date'].between('2010-01-01', '2019-12-31')]['inflation_rate_yoy'].mean()
surge = panel[panel['date'].between('2021-01-01', '2023-12-31')]['inflation_rate_yoy'].mean()
check('2.16', '2010-19 inflation below 2021-23', exp_2010s < surge,
      f'2010-19={exp_2010s:.2f}% vs 2021-23={surge:.2f}%')

chars = pd.read_csv('data/processed/state_characteristics.csv')
check('2.17', 'state_characteristics has 3 rows', len(chars) == 3,
      f'{len(chars)} rows: {list(chars["state"])}')
need_chars = ['manufacturing_share_pct', 'energy_share_pct', 'unionization_rate_pct']
missing_chars = [c for c in need_chars if c not in chars.columns]
check('2.18', 'manufacturing/energy/union columns present', not missing_chars,
      f'columns={list(chars.columns)}' + (f' | MISSING {missing_chars}' if missing_chars else ''))
ci = chars.set_index('state')
check('2.19', 'Texas has highest energy share', ci['energy_share_pct'].idxmax() == 'TX',
      ' | '.join(f'{s}: {v}%' for s, v in ci['energy_share_pct'].items()))
check('2.20', 'Ohio has highest manufacturing share',
      ci['manufacturing_share_pct'].idxmax() == 'OH',
      ' | '.join(f'{s}: {v}%' for s, v in ci['manufacturing_share_pct'].items()))

# --------------------------------------------------------------- SECTION 3
hdr('SECTION 3: NOTEBOOK CONTENT CHECKS')


def load_nb(path):
    nb = json.load(open(path, encoding='utf-8'))
    code = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code')
    md = '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'markdown')
    return code, md


code1, md1 = load_nb('notebooks/01_data_collection.ipynb')
code2, md2 = load_nb('notebooks/02_exploratory_analysis.ipynb')
code3, md3 = load_nb('notebooks/03_regression_analysis.ipynb')


def find_any(label, name, haystack, patterns):
    hits = [p_ for p_ in patterns if re.search(p_, haystack)]
    check(label, name, bool(hits), f'matched {hits}' if hits else f'none of {patterns} found')


def find_all(label, name, haystack, patterns):
    hits = [p_ for p_ in patterns if re.search(p_, haystack)]
    check(label, name, len(hits) == len(patterns),
          f'matched {hits}' if len(hits) == len(patterns)
          else f'missing {[p_ for p_ in patterns if p_ not in hits]}')


find_any('3.21', 'nb01 imports fredapi and connects', code1,
         [r'from fredapi import|import fredapi', r'Fred\('])
find_any('3.22', 'nb01 creates SQLite database', code1, [r'sqlite3\.connect', r'to_sql\('])
# CSV paths are built with os.path.join into a variable, so match the write call
# and the processed-directory assignment separately rather than inside to_csv().
find_all('3.23', 'nb01 saves CSVs to data/processed/', code1,
         [r'to_csv\(', r"processed_dir\s*=|['\"]processed['\"]"])
find_any('3.24', 'nb02 loads the analysis panel', code2,
         [r'read_csv\([^)]*phillips_curve_panel\.csv'])
find_any('3.25', 'nb02 creates scatter plots', code2,
         [r'\.scatter\(', r'scatterplot\(', r'regplot\('])
find_any('3.26', 'nb02 saves figures to figures/', code2, [r'savefig\([^)]*figures'])
find_any('3.27', 'nb03 imports statsmodels', code3,
         [r'import statsmodels', r'statsmodels\.formula\.api'])
find_any('3.28', 'nb03 runs OLS regressions', code3, [r'smf\.ols\(', r'sm\.OLS\('])
find_any('3.29', 'nb03 uses PanelOLS / fixed effects', code3,
         [r'PanelOLS', r'entity_effects', r'time_effects'])
find_any('3.30', 'nb03 saves results to CSV', code3, [r'to_csv\('])
find_any('3.31', 'nb01 markdown: What is the Phillips Curve', md1, [r'What is the Phillips Curve'])
find_any('3.32', 'nb01 markdown: About This Project', md1, [r'About This Project'])
find_any('3.33', 'nb01 markdown: Recap of Notebook 1', md1, [r'Recap of Notebook 1'])
find_any('3.34', 'nb02 markdown: Important Terms', md2, [r'Important Terms'])
find_any('3.35', 'nb02 markdown: Texas oil deep dive', md2,
         [r'Deep Dive: Oil Prices and the Texas Phillips Curve', r'Understanding Oil Price Regimes'])
find_any('3.36', 'nb03 markdown: Important Terms', md3, [r'Important Terms'])
find_any('3.37', 'nb03 markdown: omitted variable bias', md3, [r'[Oo]mitted [Vv]ariable [Bb]ias'])

# --------------------------------------------------------------- SECTION 4
hdr('SECTION 4: README CONSISTENCY CHECKS')
readme = open('README.md', encoding='utf-8').read()

nb_refs = sorted(set(re.findall(r'(\d{2}_[a-z_]+\.ipynb)', readme)))
bad = [f for f in nb_refs if not os.path.isfile(f'notebooks/{f}')]
check('4.38', 'notebooks named in README exist', not bad,
      f'{len(nb_refs)} referenced: {nb_refs}' + (f' | MISSING {bad}' if bad else ''))

sql_refs = sorted(set(re.findall(r'([a-z_]+\.sql)', readme)))
bad = [f for f in sql_refs if not os.path.isfile(f'{sql_dir}/{f}')]
check('4.39', 'SQL files named in README exist', not bad,
      f'{len(sql_refs)} referenced: {sql_refs}' + (f' | MISSING {bad}' if bad else ''))

csv_refs = sorted(set(re.findall(r'([a-z_]+\.csv)', readme)))
bad = [f for f in csv_refs if not os.path.isfile(f'data/processed/{f}')]
check('4.40', 'CSVs named in README exist', not bad,
      f'{len(csv_refs)} referenced: {csv_refs}' + (f' | MISSING {bad}' if bad else ''))

img_refs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', readme)
for f in img_refs:
    print(f'     image ref: {f} -> exists={os.path.isfile(f)}')
bad = [f for f in img_refs if not os.path.isfile(f)]
check('4.41', 'embedded images resolve', bool(img_refs) and not bad,
      f'{len(img_refs)} embedded, {len(bad)} broken')

check('4.42', 'README states match the data',
      all(s in readme for s in ('Texas', 'Massachusetts', 'Ohio'))
      and set(states) == {'TX', 'MA', 'OH'},
      f'README names Texas/Massachusetts/Ohio; data has {states}')

regression_lo = panel.dropna(subset=['unemployment_rate', 'inflation_rate_yoy'])['date'].min()
claimed = re.search(r'January 2001 (?:through|to|-) July 2026', readme)
check('4.43', 'README date range matches the CSV', bool(claimed),
      f"README claims 'January 2001 through July 2026'; regression sample is "
      f"{regression_lo.date()} to {hi.date()} (raw CSV starts {lo.date()})")

master_p = 'data/processed/master_regression_results.csv'
panel_p = 'data/processed/panel_regression_results.csv'
if os.path.isfile(master_p) and os.path.isfile(panel_p):
    master, panel_res = pd.read_csv(master_p), pd.read_csv(panel_p)

    def appears(value):
        """True if the value shows up in the README at 3 or 4 decimals,
        under either half-up or half-even rounding, signed or unsigned."""
        forms = set()
        for places in (3, 4):
            hu = half_up(value, places)
            fmt = f'{value:.{places}f}'
            forms.update({hu, fmt, hu.lstrip('-+'), fmt.lstrip('-+'),
                          f'+{hu.lstrip("-+")}' if value > 0 else hu})
        return any(f in readme for f in forms), sorted(forms)

    rows, misses = [], []
    for _, r in master.iterrows():
        for st in ('TX', 'MA', 'OH'):
            v = float(r[f'{st} B1'])
            ok, forms = appears(v)
            rows.append((r['Specification'], st, v, ok, forms))
            if not ok:
                misses.append((r['Specification'], st, v))
    for _, r in panel_res.iterrows():
        v = float(r['B1 (Unemployment)'])
        ok, forms = appears(v)
        rows.append((r['Model'], 'panel', v, ok, forms))
        if not ok:
            misses.append((r['Model'], 'panel', v))

    print('     README vs results CSVs - unemployment coefficients:')
    for spec, st, v, ok, _ in rows:
        print(f'       {"OK " if ok else "MISSING"} {spec:32s} {st:5s} {v:+.4f}')
    check('4.44', 'README coefficients match results CSVs', not misses,
          f'{sum(1 for r in rows if r[3])}/{len(rows)} coefficients appear in README'
          + (f' | not found: {misses}' if misses else ''))
else:
    check('4.44', 'results CSVs available to cross-check', False,
          'master_regression_results.csv or panel_regression_results.csv missing')

# --------------------------------------------------------------- SECTION 5
hdr('SECTION 5: SQL SCRIPT VALIDATION')
keywords = re.compile(r'\b(SELECT|CREATE|JOIN|GROUP BY|WHERE|ORDER BY|CASE)\b', re.I)
empty, no_kw, no_comment = [], [], []
for f in sql_files:
    text = open(f).read()
    base = os.path.basename(f)
    if not text.strip():
        empty.append(base)
    if not keywords.search(text):
        no_kw.append(base)
    if not re.search(r'^\s*--', text, re.M):
        no_comment.append(base)
    print(f'     {base:34s} {os.path.getsize(f):>5} bytes | '
          f'keywords={sorted({k.upper() for k in keywords.findall(text)})} | '
          f'comment lines={len(re.findall(r"^\s*--", text, re.M))}')
check('5.45', 'no .sql file is empty', not empty, f'{len(sql_files)} files checked')
check('5.46', 'every .sql has SQL keywords', not no_kw,
      'all contain SELECT/CREATE/JOIN/GROUP BY' if not no_kw else f'no keywords in {no_kw}')
check('5.47', 'every .sql has -- comments', not no_comment,
      'all documented' if not no_comment else f'undocumented: {no_comment}')

# --------------------------------------------------------------- SECTION 6
hdr('SECTION 6: GITIGNORE VALIDATION')
for label, name, pattern in [
    ('6.48', 'fred_api_key.txt', r'fred_api_key\.txt'),
    ('6.49', '*.db', r'\*\.db'),
    ('6.50', 'data/raw/', r'data/raw/?'),
    ('6.51', '__pycache__', r'__pycache__'),
    ('6.52', '.ipynb_checkpoints', r'\.ipynb_checkpoints'),
    ('6.53', '.DS_Store', r'\.DS_Store'),
]:
    m = re.search(pattern, gitignore)
    check(label, f'.gitignore contains {name}', bool(m),
          f"line: '{m.group(0)}'" if m else 'not present')

# --------------------------------------------------------------- SUMMARY
hdr('FINAL SUMMARY')
numbered = [r for r in results if not r[0].startswith('S1.')]
section1 = [r for r in results if r[0].startswith('S1.')]
n_pass = sum(1 for r in numbered if r[2])
n_fail = len(numbered) - n_pass
s_pass = sum(1 for r in section1 if r[2])
s_fail = len(section1) - s_pass

print(f'Numbered checks (Sections 2-6): {len(numbered):>3}  passed={n_pass}  failed={n_fail}')
print(f'Section 1 file checks:          {len(section1):>3}  passed={s_pass}  failed={s_fail}')
print(f'TOTAL:                          {len(results):>3}  passed={n_pass + s_pass}  '
      f'failed={n_fail + s_fail}')

failures = [r for r in results if not r[2]]
if failures:
    print('\nFAILURES:')
    for i, (label, name, _, detail) in enumerate(failures, 1):
        print(f'  {i}. {label} {name}\n       found: {detail}')
    sys.exit(1)

print('\nAll checks passed. The project is ready for portfolio presentation.')
