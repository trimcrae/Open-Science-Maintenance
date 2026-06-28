# AI-contribution policies across the scientific Python ecosystem

Survey of **34** widely-used scientific/numerical Python projects, generated on **2026-06-28** by `osm-scan` (see methodology at the end). The question: *which projects accept AI-generated / agentic contributions, and under what conditions?*

## Summary

| Stance | Projects |
|--------|---------:|
| ❌ Banned — AI/agentic contributions not accepted | 2 |
| ⚠️ Conditional — allowed only with disclosure and/or human understanding | 4 |
| ✅ Allowed — responsible, disclosed AI use permitted | 1 |
| ❔ No stated policy (silent — not permission; norms are tightening) | 27 |

**Bottom line:** 1 of 34 projects explicitly permit AI-generated contributions; 2 ban them outright. **None** were found to welcome *unreviewed, fully-autonomous* PRs — even the most permissive policies require a human who understands, reviews, and can explain every change, and who discloses tool use.

## ❌ Banned — AI/agentic contributions not accepted

- **[biopython/biopython](https://github.com/biopython/biopython)** — [policy](https://github.com/biopython/biopython/blob/HEAD/CONTRIBUTING.rst)
  - evidence: "hon). Tackling these with AI tools defeats that purpose, and such PRs will be rejected, and we will likely block repeat offenders. The `help wanted <https://github.com/biopyth"
- **[MDAnalysis/mdanalysis](https://github.com/MDAnalysis/mdanalysis)** — [policy](https://github.com/MDAnalysis/mdanalysis/blob/HEAD/AI_POLICY.md)
  - evidence: "t to periodically review this policy. ## Policy overview MDAnalysis does not accept any substantial uses of AI-generated content in contributions. AI tools may be used in l"

## ⚠️ Conditional — allowed only with disclosure and/or human understanding

- **[mne-tools/mne-python](https://github.com/mne-tools/mne-python)** — [policy](https://github.com/mne-tools/mne-python/blob/HEAD/CONTRIBUTING.md)
  - evidence: "Policy on AI Assistance in Contributions ---------------------------------------- Contributing to MNE-Python requires human judgment, contextual understanding, domain knowledge, an"
- **[networkx/networkx](https://github.com/networkx/networkx)** — [policy](https://github.com/networkx/networkx/blob/HEAD/CONTRIBUTING.rst)
  - evidence: "usage. 🔒 **Do not generate PRs using AI or LLM-based tools** unless: - You have **carefully read corresponding issues and relevant documentation**"
- **[pyvista/pyvista](https://github.com/pyvista/pyvista)** — [policy](https://github.com/pyvista/pyvista/blob/HEAD/CONTRIBUTING.rst)
  - evidence: "under The MIT License found in the repository. If you did not write the code yourself, it is your responsibility to ensure that the existing license is compatible and included in t"
- **[scikit-image/scikit-image](https://github.com/scikit-image/scikit-image)** — [policy](https://github.com/scikit-image/scikit-image/blob/HEAD/CONTRIBUTING.rst)
  - evidence: "e - Describe and link relevant context in the description - Disclose all *generative* tools (AI, LLMs, agents) that you used, see our :ref:`ai-policy` for"

## ✅ Allowed — responsible, disclosed AI use permitted

- **[pydata/xarray](https://github.com/pydata/xarray)** — [policy](https://github.com/pydata/xarray/blob/HEAD/AI_POLICY.md)
  - evidence: "dless of whether the code was written by hand, with AI assistance, or generated entirely by an AI tool. [^1]: Over-reliance on AI tools has been shown to [hinder skill formation"

## ❔ No stated policy (silent — not permission; norms are tightening)

- **[astropy/astropy](https://github.com/astropy/astropy)**
- **[astropy/astroquery](https://github.com/astropy/astroquery)**
- **[bokeh/bokeh](https://github.com/bokeh/bokeh)**
- **[dask/dask](https://github.com/dask/dask)**
- **[dmlc/xgboost](https://github.com/dmlc/xgboost)**
- **[h5py/h5py](https://github.com/h5py/h5py)**
- **[hgrecco/pint](https://github.com/hgrecco/pint)**
- **[imageio/imageio](https://github.com/imageio/imageio)**
- **[lightkurve/lightkurve](https://github.com/lightkurve/lightkurve)**
- **[matplotlib/matplotlib](https://github.com/matplotlib/matplotlib)**
- **[mwaskom/seaborn](https://github.com/mwaskom/seaborn)**
- **[nipy/nibabel](https://github.com/nipy/nibabel)**
- **[numba/numba](https://github.com/numba/numba)**
- **[numpy/numpy](https://github.com/numpy/numpy)**
- **[obspy/obspy](https://github.com/obspy/obspy)**
- **[pandas-dev/pandas](https://github.com/pandas-dev/pandas)**
- **[pymc-devs/pymc](https://github.com/pymc-devs/pymc)**
- **[pysam-developers/pysam](https://github.com/pysam-developers/pysam)**
- **[scikit-bio/scikit-bio](https://github.com/scikit-bio/scikit-bio)**
- **[scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn)**
- **[scipy/scipy](https://github.com/scipy/scipy)**
- **[scverse/anndata](https://github.com/scverse/anndata)**
- **[scverse/scanpy](https://github.com/scverse/scanpy)**
- **[statsmodels/statsmodels](https://github.com/statsmodels/statsmodels)**
- **[sunpy/sunpy](https://github.com/sunpy/sunpy)**
- **[sympy/sympy](https://github.com/sympy/sympy)**
- **[zarr-developers/zarr-python](https://github.com/zarr-developers/zarr-python)**

## Methodology & caveats

- For each repo, `osm-scan` reads any dedicated AI-policy file (`AI_POLICY.md`, `doc/contribute/ai-policy.md`, …) and the `CONTRIBUTING` file, then classifies the stance with a transparent keyword heuristic that only counts ban/allow/condition markers occurring **near an AI mention** (to avoid false positives).
- Classification is heuristic and point-in-time. **Always open the linked policy and read it before acting.** A `none` result means *no policy was found*, which is not the same as permission — several projects in this ecosystem added policies recently and more are expected to.
- Evidence snippets are short excerpts for orientation, not the full policy.

