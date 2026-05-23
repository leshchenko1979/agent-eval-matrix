# Hashline hypothesis evaluation (OpenCrabs)

Standalone report for **OpenCrabs** developers. Upstream was not involved in designing these hypotheses.

| Artifact | Description |
|----------|-------------|
| [**hashline_hypothesis_report.md**](hashline_hypothesis_report.md) | Full report: background, hypotheses, methodology, results, recommendations |
| [**hashline_hypothesis_report.ipynb**](hashline_hypothesis_report.ipynb) | Interactive charts (GitHub renders `.ipynb` natively) |
| [`reports/2026-05-23T13-22-35.666225+00-00_local-r_matrix.json`](../reports/2026-05-23T13-22-35.666225+00-00_local-r_matrix.json) | Raw matrix output (50 runs) |

**Quick verdict:** H2 fuzzy replace supported (10/10); H3 empty-hash collisions rejected (7/10); H1 inconclusive; H4 mixed.

**Regenerate figures:**

```bash
pip install -e ".[report]"
python docs/_build_report_viz.py
```
