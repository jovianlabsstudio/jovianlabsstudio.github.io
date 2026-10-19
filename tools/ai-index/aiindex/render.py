"""Génère les pages statiques de l'index (anglais, public américain) dans <out>/<path>/."""
import datetime as dt
import html
import json
from collections import defaultdict
from pathlib import Path

from .analyze import summarize

CSS = """
:root{--bg:#f7f6f2;--card:#fff;--ink:#16173a;--ink2:#55566e;--line:#e4e2da;--accent:#2a2e78;--gold:#c98f2c;--goldsoft:#f4e3bd;--bar:#d9dbf2}
@media (prefers-color-scheme:dark){:root{--bg:#0f1024;--card:#171936;--ink:#eceaf6;--ink2:#a6a8c4;--line:#2a2c52;--accent:#aab0ff;--gold:#e9c46a;--goldsoft:#3a3220;--bar:#2c2f5e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}header,main,footer{max-width:1040px;margin:0 auto;padding:0 16px}
header{display:flex;align-items:center;gap:10px;padding-top:20px}header .brand{font-weight:700;letter-spacing:.2px;color:var(--ink);text-decoration:none}
header .dot{width:22px;height:22px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#3a3f96,#1c1f5a);box-shadow:inset 0 0 0 2px var(--gold)}
h1{font-size:clamp(1.6rem,4vw,2.4rem);line-height:1.15;margin:28px 0 8px}h2{font-size:1.25rem;margin:36px 0 12px}
.lede{color:var(--ink2);max-width:720px}.banner{background:#b3261e;color:#fff;padding:10px 14px;border-radius:8px;margin-top:16px;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:22px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.kpi b{display:block;font-size:1.5rem}.kpi span{color:var(--ink2);font-size:.9rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px 14px;overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:560px}th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-size:.82rem;color:var(--ink2);font-weight:600;text-transform:uppercase;letter-spacing:.04em}tr:last-child td{border-bottom:0}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}.ci{position:relative;height:10px;background:var(--bar);border-radius:5px;min-width:140px}
.ci i{position:absolute;top:0;height:10px;background:var(--goldsoft);border:1px solid var(--gold);border-radius:5px}.ci b{position:absolute;top:-3px;width:4px;height:16px;background:var(--gold);border-radius:2px}
.small{font-size:.86rem;color:var(--ink2)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.tile{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;text-decoration:none;color:var(--ink)}
.tile:hover{border-color:var(--gold)}.tile .t{font-weight:650}.tile .s{color:var(--ink2);font-size:.9rem;margin-top:4px}
.cta{background:var(--card);border:1px solid var(--gold);border-radius:12px;padding:18px;margin:36px 0}
footer{color:var(--ink2);font-size:.85rem;padding:36px 16px 48px}details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0}
summary{cursor:pointer;font-weight:600}
"""


def esc(x):
    return html.escape(str(x), quote=True)


def pct(x):
    return f"{100 * x:.0f}%"


def page(title, desc, canonical, body, noindex=False, jsonld=None):
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(canonical)}">{robots}
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><style>{CSS}</style>{ld}</head>
<body>{body}</body></html>"""


def header(base):
    return f'<header><span class="dot"></span><a class="brand" href="{base}/">Jovian Labs · AI Recommendation Index</a></header>'


def footer(cfg, base):
    return (f'<footer><p>Jovian Labs measures what AI assistants answer; it does not endorse or rank businesses on quality. '
            f'Answers vary between runs and users. <a href="{base}/methodology/">Methodology</a> · '
            f'Contact: <a href="mailto:{esc(cfg["contact_email"])}">{esc(cfg["contact_email"])}</a></p></footer>')


def load(data_dir, weeks, mock):
    files = sorted(p for p in Path(data_dir).glob("*.json") if p.stem.endswith("-mock") == mock)
    files = files[-weeks:]
    payloads = [json.loads(p.read_text()) for p in files]
    labels = {}
    for pl in payloads:
        labels.update(pl.get("engines", {}))
    return payloads, labels


def build(cfg, data_dir, out_root, mock=False):
    payloads, labels = load(data_dir, cfg.get("rolling_weeks", 4), mock)
    if not payloads:
        raise SystemExit("no data")
    base = f"/{cfg['path']}"
    site = cfg["site_base"].rstrip("/") + base
    out = Path(out_root) / cfg["path"]
    out.mkdir(parents=True, exist_ok=True)
    period = f"{payloads[0]['week']} to {payloads[-1]['week']}" if len(payloads) > 1 else payloads[-1]["week"]
    updated = payloads[-1]["date"]
    groups = defaultdict(list)
    for pl in payloads:
        for r in pl["records"]:
            groups[(r["category"], r["city"])].append(r)
    banner = '<div class="banner">TEST DATA: simulated answers, not real AI results. This page is not indexed.</div>' if mock else ""
    eng_txt = " and ".join(labels.get(e, e) for e in sorted(labels))
    summaries, urls = {}, []
    for cat in cfg["categories"]:
        for city in cfg["cities"]:
            recs = groups.get((cat["slug"], city["slug"]))
            if not recs:
                continue
            sm = summarize(recs, labels)
            summaries[(cat["slug"], city["slug"])] = sm
            place = f"{city['name']}, {city['state']}"
            title = f"Which {cat['plural']} do AI assistants recommend in {place}? | AI Recommendation Index"
            desc = (f"Measured weekly: the {cat['plural']} that Gemini and Perplexity name when asked for the best {cat['singular']} "
                    f"in {place}, with mention rates and 95% confidence intervals.")
            url = f"{site}/{cat['slug']}/{city['slug']}/"
            urls.append(url)
            rows = []
            for i, r in enumerate(sm["rows"][:20], 1):
                eng = " · ".join(f"{labels.get(e, e).split(' (')[0]} {k}/{n}" for e, (k, n) in sorted(r["engines"].items()))
                rows.append(f"<tr><td class='num'>{i}</td><td><b>{esc(r['name'])}</b><div class='small'>{esc(eng)}</div></td>"
                            f"<td class='num'>{pct(r['rate'])}<div class='small'>{r['mentions']} of {r['answers']} answers</div></td>"
                            f"<td><div class='ci' title='95% CI {pct(r['ci_low'])} to {pct(r['ci_high'])}'><i style='left:{100 * r['ci_low']:.1f}%;width:{max(1.5, 100 * (r['ci_high'] - r['ci_low'])):.1f}%'></i>"
                            f"<b style='left:calc({100 * r['rate']:.1f}% - 2px)'></b></div><div class='small'>{pct(r['ci_low'])} to {pct(r['ci_high'])}</div></td>"
                            f"<td class='num'>{r['first_rank']}</td></tr>")
            doms = "".join(f"<tr><td>{esc(d)}</td><td class='num'>{pct(s)}</td></tr>" for d, _, s in sm["top_domains"])
            body = f"""{header(base)}<main>{banner}
<h1>Which {esc(cat['plural'])} do AI assistants recommend in {esc(place)}?</h1>
<p class="lede">We ask {esc(eng_txt)} the questions people really type, such as “Who is the best {esc(cat['singular'])} in {esc(place)}?”,
several times a week, and count which businesses they name. Period: {esc(period)}. Updated {esc(updated)}.</p>
<div class="kpis"><div class="kpi"><b>{sm['answers']}</b><span>AI answers analysed</span></div>
<div class="kpi"><b>{sm['distinct_businesses']}</b><span>different businesses named</span></div>
<div class="kpi"><b>{pct(sm['top3_share'])}</b><span>of answers name one of the top 3</span></div>
<div class="kpi"><b>{pct(sm['answers_without_business'] / max(1, sm['answers']))}</b><span>answers name no specific business</span></div></div>
<h2>Businesses named by AI assistants</h2>
<div class="card"><table><thead><tr><th>#</th><th>Business</th><th>Mention rate</th><th>95% confidence interval</th><th>Named first</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan=5>No business named yet.</td></tr>'}</tbody></table></div>
<p class="small">Mention rate = share of answers that name the business. The interval shows the range compatible with the sample: when two intervals overlap, the difference may be noise.</p>
<h2>Where the AI assistants look</h2>
<div class="card"><table><thead><tr><th>Source cited</th><th>Share of answers</th></tr></thead><tbody>{doms or '<tr><td colspan=2>No sources returned.</td></tr>'}</tbody></table></div>
<div class="cta"><b>Is your business in AI answers?</b><p class="small">We can run the same measurement for your business, your competitors and your own questions,
across more AI assistants. Write to <a href="mailto:{esc(cfg['contact_email'])}">{esc(cfg['contact_email'])}</a>.</p></div>
<h2>Questions</h2>
<details><summary>Does this mean these {esc(cat['plural'])} are the best?</summary><p>No. It measures what AI assistants say, not service quality. AI answers can be incomplete or outdated.</p></details>
<details><summary>Why do the results change from one answer to the next?</summary><p>AI assistants do not give the same answer every time. That is why we sample each question several times and report confidence intervals.</p></details>
<details><summary>How can a business appear more often?</summary><p>The answers rely on the sources listed above: being present and well reviewed there is a good start. See the <a href="{base}/methodology/">methodology</a>.</p></details>
</main>{footer(cfg, base)}"""
            jsonld = {"@context": "https://schema.org", "@type": "Dataset", "name": f"AI assistant recommendations for {cat['plural']} in {place}",
                      "description": desc, "url": url, "temporalCoverage": period, "creator": {"@type": "Organization", "name": "Jovian Labs"},
                      "variableMeasured": "Share of AI answers naming each business"}
            p = out / cat["slug"] / city["slug"] / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(page(title, desc, url, body, noindex=mock, jsonld=jsonld), encoding="utf-8")
    # index
    tiles = []
    for cat in cfg["categories"]:
        t = []
        for city in cfg["cities"]:
            sm = summaries.get((cat["slug"], city["slug"]))
            if not sm:
                continue
            top = sm["rows"][0] if sm["rows"] else None
            s = f"Most named: {esc(top['name'])} ({pct(top['rate'])})" if top else "No business named"
            t.append(f"<a class='tile' href='{base}/{cat['slug']}/{city['slug']}/'><div class='t'>{esc(city['name'])}, {esc(city['state'])}</div><div class='s'>{s}</div></a>")
        tiles.append(f"<h2>{esc(cat['label'])}</h2><div class='grid'>{''.join(t)}</div>")
    body = f"""{header(base)}<main>{banner}<h1>Which local businesses do AI assistants recommend?</h1>
<p class="lede">More and more people ask ChatGPT-style assistants “who is the best plumber near me?”. The AI Recommendation Index measures, every week,
which businesses {esc(eng_txt)} actually name in large US cities, with confidence intervals. Period: {esc(period)}. Updated {esc(updated)}.</p>
{''.join(tiles)}<div class="cta"><b>Want this for your business or your clients?</b><p class="small">Custom tracking of your brand, your competitors and your own questions:
<a href="mailto:{esc(cfg['contact_email'])}">{esc(cfg['contact_email'])}</a>.</p></div></main>{footer(cfg, base)}"""
    (out / "index.html").write_text(page("AI Recommendation Index: which local businesses do AI assistants recommend?",
                                         "Weekly measurement of the businesses Gemini and Perplexity recommend in US cities, with confidence intervals.",
                                         f"{site}/", body, noindex=mock), encoding="utf-8")
    urls.insert(0, f"{site}/")
    # méthodologie
    q = "".join(f"<li>{esc(t)}</li>" for t in cfg["prompts"])
    body = f"""{header(base)}<main><h1>Methodology</h1>
<p class="lede">How the AI Recommendation Index is measured, and what it does not say.</p>
<h2>Questions</h2><p>For each category and city we ask {len(cfg['prompts'])} wordings, each {cfg.get('samples_per_prompt', 2)} times per assistant and per week:</p><ul>{q}</ul>
<h2>Assistants</h2><p>{esc(eng_txt)}, through their official APIs with live web search. Consumer apps may answer differently,
for example because of location, history or personalization.</p>
<h2>Counting</h2><p>Each answer is read by a language model that lists the businesses it names (directories such as Yelp or Google are excluded).
Variants of the same name are merged. The mention rate is the share of answers naming the business, pooled over the last {cfg.get('rolling_weeks', 4)} weekly runs.</p>
<h2>Uncertainty</h2><p>AI answers vary from one run to the next. We report 95% Wilson confidence intervals: if two businesses' intervals overlap,
their difference may be noise.</p>
<h2>Limits</h2><p>This measures visibility in AI answers, not quality. Names can be misread or invented by the assistants; open the business's own website before relying on it.
Jovian Labs is independent and not affiliated with Google, Perplexity or any business listed.</p></main>{footer(cfg, base)}"""
    m = out / "methodology" / "index.html"
    m.parent.mkdir(parents=True, exist_ok=True)
    m.write_text(page("Methodology | AI Recommendation Index", "How the AI Recommendation Index measures AI assistant recommendations.",
                      f"{site}/methodology/", body, noindex=mock), encoding="utf-8")
    urls.append(f"{site}/methodology/")
    if not mock:
        today = dt.date.today().isoformat()
        sm = "".join(f"<url><loc>{esc(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
        (out / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    (out / "data.json").write_text(json.dumps({f"{k[0]}/{k[1]}": v for k, v in summaries.items()}, ensure_ascii=False, indent=1))
    print(f"{len(summaries)} pages -> {out}")
    return out
