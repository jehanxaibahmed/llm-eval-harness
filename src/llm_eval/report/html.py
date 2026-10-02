"""Self-contained HTML report: inline CSS/SVG, light and dark themes, hover tooltips."""

from __future__ import annotations

from html import escape

from llm_eval.report.insights import Insights
from llm_eval.report.markdown import pct, secs, usd

# Categorical slots in fixed order (light, dark). The first three validate all-pairs for CVD
# separation in both modes; beyond eight models, bars fall back to neutral with direct labels.
SERIES = [
    ("#2a78d6", "#3987e5"),
    ("#eb6834", "#d95926"),
    ("#1baf7a", "#199e70"),
    ("#eda100", "#c98500"),
    ("#e87ba4", "#d55181"),
    ("#008300", "#008300"),
    ("#4a3aa7", "#9085e9"),
    ("#e34948", "#e66767"),
]

CSS = """
:root{color-scheme:light;--bg:#f6f6f4;--surface:#fcfcfb;--border:#e4e3df;--grid:#ecebe7;
--text:#0b0b0b;--text-2:#52514e;--muted:#8a8984;--accent:#2a78d6;--other:#a3a29c;SERIES_LIGHT}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;--grid:#262624;--text:#fff;--text-2:#c3c2b7;
--muted:#8f8e86;--accent:#3987e5;--other:#6b6a64;SERIES_DARK}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121211;--surface:#1a1a19;--border:#2e2e2b;
--grid:#262624;--text:#fff;--text-2:#c3c2b7;--muted:#8f8e86;--accent:#3987e5;--other:#6b6a64;
SERIES_DARK}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 12px}
h3{font-size:15px;margin:20px 0 8px;color:var(--text-2)}
.meta{color:var(--text-2);font-size:13px;margin:0 0 24px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;
margin:12px 0}
.picks{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.pick .k{font-size:12px;color:var(--text-2);text-transform:uppercase;letter-spacing:.04em}
.pick .v{font-size:17px;font-weight:600;display:flex;align-items:center;gap:8px}
.sw{width:10px;height:10px;border-radius:3px;display:inline-block;flex:none}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:var(--text-2);margin:4px 0 8px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.chart h4{margin:0 0 2px;font-size:14px}.chart p{margin:0 0 8px;font-size:12px;color:var(--muted)}
.chart .row{display:grid;grid-template-columns:minmax(80px,38%) 1fr;align-items:center;gap:8px;
padding:4px 6px;margin:0 -6px;border-radius:6px;font-size:12px}
.chart .row:hover{background:var(--grid)}
.chart .lbl{color:var(--text-2);text-align:right;overflow:hidden;text-overflow:ellipsis;
white-space:nowrap}
.chart .track{display:flex;align-items:center;gap:6px;border-left:1px solid var(--border);
min-height:18px}
.chart .bar{display:block;height:16px;min-width:2px;border-radius:0 4px 4px 0}
.chart .val{color:var(--text);font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:7px 10px;border-bottom:1px solid var(--border);text-align:right;white-space:nowrap}
th{color:var(--text-2);font-weight:600}th:first-child,td:first-child{text-align:left}
td.l,th.l{text-align:left}
code{font:12px ui-monospace,SFMono-Regular,Menlo,monospace}
.fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.fields ul{margin:0;padding:0;list-style:none;font-size:13px}
.fields li{display:flex;justify-content:space-between;gap:8px;padding:3px 0;
border-bottom:1px dashed var(--border)}
#tip{position:fixed;pointer-events:none;background:var(--text);color:var(--surface);
font-size:12px;padding:6px 8px;border-radius:6px;opacity:0;transition:opacity .08s;
white-space:pre;z-index:10}
"""

TIP_JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el=>{
 el.addEventListener('mousemove',e=>{tip.textContent=el.dataset.tip;tip.style.opacity=1;
  const x=Math.min(e.clientX+12,innerWidth-tip.offsetWidth-8);
  tip.style.left=x+'px';tip.style.top=(e.clientY+14)+'px';});
 el.addEventListener('mouseleave',()=>{tip.style.opacity=0;});
});
"""


def _series_var(idx: int) -> str:
    return f"var(--s{idx + 1})" if idx < len(SERIES) else "var(--other)"


def _bar_chart(title: str, note: str, rows: list[tuple[str, int, float, str]], vmax: float) -> str:
    """Horizontal bars, one per model. rows: (label, series index, value, formatted value)."""
    vmax = vmax or 1.0
    bars = []
    for label, sidx, value, shown in rows:
        frac = max(0.0, min(1.0, value / vmax))
        tip = escape(f"{label}\n{title}: {shown}")
        bars.append(
            f'<div class="row" data-tip="{tip}"><span class="lbl">{escape(label)}</span>'
            f'<span class="track"><span class="bar" style="width:calc((100% - 76px) * {frac:.4f});'
            f'background:{_series_var(sidx)}"></span><span class="val">{shown}</span></span></div>'
        )
    return (
        f'<div class="card chart" role="figure" aria-label="{escape(title)}">'
        f"<h4>{escape(title)}</h4><p>{escape(note)}</p>" + "".join(bars) + "</div>"
    )


def render_html(ins: Insights) -> str:
    color = {m: i for i, m in enumerate(ins.models)}
    series_light = "".join(f"--s{i + 1}:{lt};" for i, (lt, _) in enumerate(SERIES))
    series_dark = "".join(f"--s{i + 1}:{dk};" for i, (_, dk) in enumerate(SERIES))
    css = CSS.replace("SERIES_LIGHT", series_light).replace("SERIES_DARK", series_dark)

    def swatch(model: str) -> str:
        return f'<i class="sw" style="background:{_series_var(color.get(model, 99))}"></i>'

    legend = (
        '<div class="legend">'
        + "".join(f"<span>{swatch(m)}{escape(m)}</span>" for m in ins.models)
        + "</div>"
    )

    started = ins.started_at[:19].replace("T", " ")
    body = [
        f"<h1>Model comparison: {escape(ins.config_name)}</h1>",
        f'<p class="meta">Run <code>{escape(ins.run_id)}</code> · {len(ins.models)} models'
        f" · {len(ins.suites)} suites · started {escape(started)} UTC</p>",
        "<h2>Overall</h2>",
        legend,
        '<div class="card tablewrap"><table><thead><tr><th>Model</th><th>Field accuracy</th>'
        "<th>Exact match</th><th>Valid JSON</th><th>Latency p50</th><th>Total cost</th>"
        "</tr></thead><tbody>",
    ]
    for r in ins.overall.itertuples():
        body.append(
            f"<tr><td>{swatch(r.model)} {escape(r.model)}</td><td>{pct(r.field_accuracy)}</td>"
            f"<td>{pct(r.exact_match_rate)}</td><td>{pct(r.json_valid_rate)}</td>"
            f"<td>{secs(r.latency_p50_s)}</td><td>{usd(r.total_cost_usd)}</td></tr>"
        )
    body.append("</tbody></table></div>")

    for suite in ins.suites:
        s = suite.summary
        body.append(f"<h2>{escape(suite.name)}</h2>")
        if suite.picks:
            body.append('<div class="picks">')
            for k, m in suite.picks.items():
                body.append(
                    f'<div class="card pick"><div class="k">{escape(k)}</div>'
                    f'<div class="v">{swatch(m)}{escape(m)}</div></div>'
                )
            body.append("</div>")

        def rows(col: str, fmt, frame=s):
            return [
                (r["model"], color[r["model"]], float(r[col]), fmt(r[col]))
                for _, r in frame.iterrows()
            ]

        body.append('<div class="charts">')
        body.append(
            _bar_chart(
                "Field accuracy",
                "Share of expected fields extracted correctly",
                rows("field_accuracy", pct),
                1.0,
            )
        )
        body.append(
            _bar_chart(
                "Cost per document",
                "Mean USD per call; lower is better",
                rows("cost_per_doc_usd", usd),
                float(s["cost_per_doc_usd"].max()),
            )
        )
        body.append(
            _bar_chart(
                "Latency p50",
                "Median seconds per call; lower is better",
                rows("latency_p50_s", secs),
                float(s["latency_p50_s"].max()),
            )
        )
        body.append("</div>")

        body.append(
            '<div class="card tablewrap"><table><thead><tr><th>Model</th><th>Field acc.</th>'
            "<th>Exact match</th><th>Valid JSON</th><th>p50</th><th>p95</th><th>Cost/doc</th>"
            "<th>Errors</th></tr></thead><tbody>"
        )
        for r in s.itertuples():
            body.append(
                f"<tr><td>{swatch(r.model)} {escape(r.model)}</td><td>{pct(r.field_accuracy)}</td>"
                f"<td>{pct(r.exact_match_rate)}</td><td>{pct(r.json_valid_rate)}</td>"
                f"<td>{secs(r.latency_p50_s)}</td><td>{secs(r.latency_p95_s)}</td>"
                f"<td>{usd(r.cost_per_doc_usd)}</td><td>{r.errors}</td></tr>"
            )
        body.append("</tbody></table></div>")

        body.append('<h3>Weakest fields</h3><div class="fields">')
        for model, df in suite.weakest_fields.items():
            items = (
                "".join(
                    f"<li><code>{escape(r.field)}</code><span>{pct(r.accuracy)}</span></li>"
                    for r in df.itertuples()
                )
                or "<li>Every field 100% correct</li>"
            )
            body.append(
                f'<div class="card"><h4>{swatch(model)} {escape(model)}</h4><ul>{items}</ul></div>'
            )
        body.append("</div>")

        if not suite.failures.empty:
            body.append(
                '<h3>Lowest-scoring cases</h3><div class="card tablewrap"><table><thead><tr>'
                '<th>Model</th><th class="l">Case</th><th>Accuracy</th><th>Valid JSON</th>'
                '<th class="l">Error</th></tr></thead><tbody>'
            )
            for r in suite.failures.itertuples():
                err = escape(r.error) if isinstance(r.error, str) else ""
                body.append(
                    f"<tr><td>{swatch(r.model)} {escape(r.model)}</td>"
                    f'<td class="l"><code>{escape(r.case_id)}</code></td>'
                    f"<td>{pct(r.accuracy)}</td><td>{'yes' if r.json_valid else 'no'}</td>"
                    f'<td class="l">{err}</td></tr>'
                )
            body.append("</tbody></table></div>")

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Eval Report</title><style>{css}</style></head><body><main>"
        + "\n".join(body)
        + f'</main><div id="tip" role="tooltip"></div><script>{TIP_JS}</script></body></html>'
    )
