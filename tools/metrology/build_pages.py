"""Pages « Metrology » du site (statiques) : hub, granulométrie + dépistage nano, porosité, guide de la définition UE.

python tools/metrology/build_pages.py  (depuis la racine du dépôt) -> metrology/**/index.html, metrologie/…, metrology/sitemap.xml
Contenu rédigé à la main ici ; les rapports d'exemple sont dans metrology/examples/ (démos synthétiques).
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://jovianlabsstudio.github.io"
APIFY_PS = "https://apify.com/jovianlabs/sem-tem-particle-size"
APIFY_PO = "https://apify.com/jovianlabs/porosity-analyzer"
APIFY_FI = "https://apify.com/jovianlabs/fiber-diameter-analyzer"
MAIL = "jovianlabsstudio@gmail.com"


def page(path, title, desc, body, lang="en", jsonld=None, alt=None):
    url = f"{SITE}/{path}"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    alts = "".join(f'<link rel="alternate" hreflang="{h}" href="{SITE}/{p}">' for h, p in (alt or {}).items())
    nav = ('<nav><a href="/metrology/">Metrology</a><a href="/tenders/">Tenders</a><a href="/ai-index/">AI Index</a>'
           f'<a href="mailto:{MAIL}">Contact</a></nav>')
    html = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">
<link rel="canonical" href="{url}">{alts}<link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<link rel="stylesheet" href="/assets/style.css">{ld}</head><body>
<header><a class="brand" href="/"><img src="/assets/logo.svg" alt="">Jovian Labs</a>{nav}</header>
<main>{body}</main>
<footer>© Jovian Labs. Independent; not affiliated with Apify, the European Commission or any standards body.
Automated image analysis, not an accredited (ISO/IEC 17025) measurement.</footer></body></html>"""
    out = ROOT / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return url


def app_ld(name, desc, url, apify):
    return {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": name, "description": desc,
            "url": url, "applicationCategory": "ScientificApplication", "operatingSystem": "Web",
            "offers": {"@type": "Offer", "price": "1.00", "priceCurrency": "USD",
                       "description": "per image analysed; demo runs are free"},
            "sameAs": [apify], "publisher": {"@type": "Organization", "name": "Jovian Labs", "url": f"{SITE}/"}}


def faq_ld(pairs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}


def faq_html(pairs):
    return "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in pairs)


def build():
    urls = []

    # ------------------------------------------------------------------ hub
    body = f"""<h1>Microscopy image analysis, with the uncertainty attached.</h1>
<p class="lede">Upload electron or optical micrographs and get a measurement you can file: statistics with confidence intervals,
automatic quality checks, a control image and a PDF report. Each tool runs on demand, is paid per image, and has a free demo
on synthetic images whose true values are known.</p>
<div class="grid">
<a class="tile" href="/metrology/particle-size/"><div class="k">SEM / TEM · powders & nanoparticles</div>
<div class="t">Particle size & EU nanomaterial screening</div>
<div class="s">D10/D50/D90 with 95% confidence intervals, Feret diameters, and the share of particles at or below 100 nm with a
meets / not met / borderline verdict.</div></a>
<a class="tile" href="/metrology/porosity/"><div class="k">Metallography · AM, castings, coatings</div>
<div class="t">Porosity of polished cross-sections</div>
<div class="s">Area porosity with 95% confidence interval and relative accuracy, pore sizes, largest pores, round vs
lack-of-fusion pores.</div></a>
<a class="tile" href="/metrology/fiber-diameter/"><div class="k">SEM · electrospinning & filters</div>
<div class="t">Fiber diameter</div>
<div class="s">Length-weighted diameter distribution with 95% confidence interval, measured like a CD-SEM line width,
plus beads and fiber alignment.</div></a>
<a class="tile" href="/metrology/eu-nanomaterial-definition/"><div class="k">Guide</div>
<div class="t">The EU nanomaterial definition, explained</div>
<div class="s">What the 2022 Recommendation says, why electron microscopy is used, and how to read a screening result.</div></a>
</div>
<h2>How these tools differ</h2>
<ul>
<li><b>Uncertainty first.</b> Every headline number comes with its confidence interval, and the tools say when a result is too
close to a threshold to conclude.</li>
<li><b>Checks you can see.</b> Each run rates itself green, amber or red on scale consistency, sample size, contrast and more, and
outlines every detected object on a control image.</li>
<li><b>Traceable.</b> The report carries the engine version, parameters and SHA-256 fingerprints of the images: the same images
always give the same numbers.</li>
<li><b>No installation, no licence.</b> Pay per image on Apify, or call the tools from scripts and AI agents through the Apify API
and MCP server.</li>
</ul>
<div class="cta"><b>Need a reviewed report?</b><p class="small">A materials imaging scientist can check the outlines and sign the
report. Write to <a href="mailto:{MAIL}">{MAIL}</a>.</p></div>"""
    urls.append(page("metrology/", "Microscopy image analysis tools: particle size, nanomaterial screening, porosity | Jovian Labs",
                     "Online SEM/TEM particle size analysis with EU nanomaterial screening, fiber diameter measurement and porosity "
                     "of polished cross-sections, with confidence intervals, quality checks and PDF reports.", body))

    # ------------------------------------------------------------------ particle size
    faq = [
        ("Which images can I use?", "SEM or TEM images of one sample, all at the same magnification, as TIFF, PNG or JPG. Original "
         "Zeiss or Thermo Fisher TIFF files are calibrated from their metadata; otherwise give the scale bar length or the pixel size."),
        ("How many particles should I measure?", "At least 300 for a size distribution and 500 for the nanomaterial screening. The "
         "report shows the precision reached on D50 and how many particles a ±2 % precision would need."),
        ("Is the nanomaterial verdict a regulatory determination?", "No. It screens criterion (a) of the EU definition on the particles "
         "measured, with its uncertainty. It does not assess the volume specific surface area, dimensions below 1 nm or the thickness "
         "of platelets lying flat."),
        ("What does it cost?", "1 US dollar per image analysed, billed by Apify. Demo runs on synthetic images are free."),
    ]
    body = f"""<h1>SEM/TEM particle size analysis with EU nanomaterial screening</h1>
<p class="lede">Turn electron microscope images into a particle size distribution report in about ten seconds per image:
D10, D50 and D90 with 95% confidence intervals, minimum and maximum Feret diameters, shape factors, nine automatic quality checks
and a screening against the EU definition of nanomaterial.</p>
<p><a class="tag hot" href="{APIFY_PS}">Run it on Apify</a> &nbsp; <a class="tag" href="/metrology/examples/particle-size-demo-report.pdf">Example report (PDF)</a></p>
<h2>EU nanomaterial screening</h2>
<p>Under Commission Recommendation 2022/C 229/01, a material meets criterion (a) when 50% or more of its particles, counted by
number, have at least one external dimension between 1 and 100 nm. Each run reports the share of particles whose minimum Feret
diameter is 100 nm or less, a Wilson confidence interval, a wider interval that adds calibration error and edge blur, the median
minimum Feret, and a verdict: <b>meets</b>, <b>not met</b>, or <b>borderline</b> when the interval includes 50%.
<a href="/metrology/eu-nanomaterial-definition/">Read the guide</a>.</p>
<h2>What you get</h2>
<div class="card"><table><thead><tr><th>Output</th><th>Content</th></tr></thead><tbody>
<tr><td>PDF report</td><td>Results and confidence intervals, nanomaterial screening, distribution and cumulative curve, results per
image, quality checks, method, traceability</td></tr>
<tr><td>Per-particle CSV</td><td>Status, equivalent diameter, min/max Feret, aspect ratio, circularity, solidity, position</td></tr>
<tr><td>Control sheet</td><td>Every image with the detected outlines</td></tr>
<tr><td>JSON and dataset row</td><td>All statistics in machine-readable form, for scripts, spreadsheets and AI agents</td></tr>
</tbody></table></div>
<h2>Accuracy</h2>
<ul><li>Synthetic SEM images with known sizes (the free demo): 580 particles measured for 578 present, D50 within +3.7% of the truth.</li>
<li>Nanomaterial screening on synthetic samples with a known share at or below 100 nm (96%, 70%, 62%, 10%): measured within 1 to 6
points, always inside the reported interval; the 62% sample is correctly reported as borderline.</li>
<li>Limit: strongly agglomerated powders read high, and the agglomerate check turns amber or red.</li></ul>
<h2>Control sheet from the demo</h2>
<p><img src="/metrology/examples/particle-size-control-sheet.jpg" alt="Synthetic SEM images with detected particle outlines"
style="max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line)"></p>
<h2>Questions</h2>{faq_html(faq)}
<div class="cta"><b>Try it free</b><p class="small">Open the <a href="{APIFY_PS}">Actor on Apify</a> and press Start with an empty
image list: it analyses three synthetic images and compares the result with the truth.</p></div>"""
    urls.append(page("metrology/particle-size/", "SEM/TEM particle size analysis online, with EU nanomaterial screening | Jovian Labs",
                     "Upload SEM or TEM images and get D10/D50/D90 with 95% confidence intervals, Feret diameters, quality checks, "
                     "a PDF report and an EU nanomaterial definition screening. 1 USD per image, free demo.",
                     body, jsonld=[app_ld("SEM/TEM Particle Size & Nanomaterial Screening",
                                          "Particle size distribution and EU nanomaterial screening from electron microscope images.",
                                          f"{SITE}/metrology/particle-size/", APIFY_PS), faq_ld(faq)]))

    # ------------------------------------------------------------------ porosity
    faq = [
        ("Which images can I use?", "Polished, unetched cross-sections imaged in bright-field optical microscopy or SEM, with pores "
         "darker than the material (or tick the option for bright pores). Give the pixel size, the scale bar length, or send original "
         "Zeiss or Thermo Fisher SEM TIFF files."),
        ("How many fields?", "Five or more, spread over the section. The report gives the relative accuracy reached and how many fields "
         "would bring it to 10%."),
        ("Does it separate gas pores from lack-of-fusion pores?", "It types each pore from its roundness: round (gas or keyhole), "
         "irregular (likely lack of fusion) or intermediate. The thresholds are adjustable because they depend on the alloy and "
         "process; typing on a 2D section is indicative."),
        ("What about mounting resin and uneven lighting?", "Large dark regions touching the field border are excluded from the material, "
         "and uneven illumination is corrected before thresholding."),
        ("What does it cost?", "1 US dollar per image analysed, billed by Apify. Demo runs on synthetic sections are free."),
    ]
    body = f"""<h1>Porosity analysis of polished cross-sections</h1>
<p class="lede">For metal additive manufacturing, castings, sintered parts and thermal spray coatings: upload micrographs of a
cross-section and get the area porosity with its 95% confidence interval and relative accuracy, the pore size distribution, the
largest pores with their position, the share of round and lack-of-fusion pores, eight quality checks and a PDF report.</p>
<p><a class="tag hot" href="{APIFY_PO}">Run it on Apify</a> &nbsp; <a class="tag" href="/metrology/examples/porosity-demo-report.pdf">Example report (PDF)</a></p>
<h2>Built for porosity, not adapted from a generic tool</h2>
<ul>
<li><b>Prudent threshold.</b> The lower of the Otsu threshold and the noise limit of the material, so that grain contrast and polishing
scratches are not counted as pores when porosity is low. The report states how much the result moves if the threshold moves.</li>
<li><b>Illumination correction</b> for the darker corners of optical microscopes.</li>
<li><b>Mounting resin excluded</b> instead of being counted as a giant pore.</li>
<li><b>Field statistics</b> as in quantitative metallography: mean, 95% confidence interval, relative accuracy %RA and the number of
fields needed for 10%.</li>
</ul>
<h2>Accuracy on synthetic cross-sections</h2>
<div class="card"><table><thead><tr><th>True porosity</th><th>Measured</th><th>Pores counted</th><th>Largest pore</th></tr></thead><tbody>
<tr><td class="num">0.59%</td><td class="num">0.59%</td><td class="num">29 of 29</td><td class="num">137.0 µm (true 138.6)</td></tr>
<tr><td class="num">2.17%</td><td class="num">2.19%</td><td class="num">104 of 104</td><td class="num">152.7 µm (true 152.8)</td></tr>
<tr><td class="num">6.16%</td><td class="num">6.21%</td><td class="num">244 of 244</td><td class="num">153.7 µm (true 154.0)</td></tr>
</tbody></table></div>
<p class="small">With corners 35% darker, the illumination correction gives 2.17% for a true 2.14%, where a plain threshold reads 1.83%.</p>
<h2>Control sheet from the demo</h2>
<p><img src="/metrology/examples/porosity-control-sheet.jpg" alt="Synthetic cross-sections with pores outlined by type"
style="max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line)"></p>
<h2>Questions</h2>{faq_html(faq)}
<p class="small">Limits: oxides, inclusions or dark phases as dark as pores are counted as pores; preparation artefacts (pull-outs,
smearing) are not detected automatically; a 2D section does not give volume porosity (use CT or the Archimedes method).</p>"""
    urls.append(page("metrology/porosity/", "Porosity analysis online for AM, castings and coatings cross-sections | Jovian Labs",
                     "Measure area porosity from polished cross-section micrographs: porosity % with 95% confidence interval, "
                     "relative accuracy, pore sizes, largest pores, gas vs lack-of-fusion pores and a PDF report.",
                     body, jsonld=[app_ld("Porosity Analyzer for Metallography (AM & Coatings)",
                                          "Area porosity and pore analysis from polished cross-section micrographs.",
                                          f"{SITE}/metrology/porosity/", APIFY_PO), faq_ld(faq)]))

    # ------------------------------------------------------------------ fibres
    faq = [
        ("Which images can I use?", "SEM images of one sample at the same magnification, with at least 8 pixels across a typical "
         "fiber, as TIFF, PNG or JPG. Original Zeiss or Thermo Fisher TIFF files are calibrated from their metadata; otherwise give "
         "the scale bar length or the pixel size."),
        ("How is the diameter measured?", "At each point of the fiber axis, on the intensity profile perpendicular to the fiber: the "
         "full width at half maximum between the local background and the peak, with sub-pixel interpolation, as a CD-SEM measures a "
         "line width. Crossings, fiber ends and beads are excluded."),
        ("Are beads counted?", "Yes, with a prudent rule: the count is a lower bound, because beads on a crossing or under other "
         "fibers are not counted."),
        ("How does it compare with DiameterJ or manual ImageJ measurements?", "It uses the same idea as DiameterJ (fiber axis and "
         "local width) but measures the width on the grey-level profile instead of a binary mask, weights by length, and gives a "
         "confidence interval from a bootstrap over fiber segments. No installation is needed."),
        ("What does it cost?", "1 US dollar per image analysed, billed by Apify. Demo runs on synthetic images are free."),
    ]
    body = f"""<h1>Fiber diameter analysis from SEM images</h1>
<p class="lede">For electrospun nanofiber mats, filter media, nonwovens and scaffolds: upload SEM images and get the length-weighted
diameter distribution with its 95% confidence interval, D10/D50/D90, beads, fiber alignment, eight quality checks and a PDF
report. No more drawing 100 lines by hand.</p>
<p><a class="tag hot" href="{APIFY_FI}">Run it on Apify</a> &nbsp; <a class="tag" href="/metrology/examples/fiber-diameter-demo-report.pdf">Example report (PDF)</a></p>
<h2>Measured like a line width, not guessed from a threshold</h2>
<p>Most automatic tools measure fibers on a black-and-white mask, so the result moves with the threshold. Here the fiber axis is
traced, and at each point the width is read on the grey-level profile across the fiber, at half maximum, to a fraction of a pixel.
On isolated fibers 8 to 40 pixels wide it reads within 0.6 pixel of the truth.</p>
<h2>Accuracy on synthetic nanofiber mats</h2>
<div class="card"><table><thead><tr><th>Case</th><th>True mean</th><th>Measured</th><th>95% CI</th></tr></thead><tbody>
<tr><td>Demo, 28 fibers per image</td><td class="num">295 nm</td><td class="num">292 nm</td><td class="num">284–300 nm</td></tr>
<tr><td>Dense mat, 38 fibers per image</td><td class="num">299 nm</td><td class="num">295 nm</td><td class="num">287–304 nm</td></tr>
<tr><td>Thin fibers, about 7 px across</td><td class="num">148 nm</td><td class="num">153 nm</td><td class="num">150–156 nm</td></tr>
<tr><td>Aligned mat</td><td class="num">305 nm</td><td class="num">302 nm</td><td class="num">293–311 nm</td></tr>
</tbody></table></div>
<p class="small">Limit: in very dense mats of thick fibers, fibers partly hidden by others read too thin, and the run flags a large
share of excluded axis.</p>
<h2>Control sheet from the demo</h2>
<p><img src="/metrology/examples/fiber-control-sheet.jpg" alt="Synthetic nanofiber images with measured axes, crossings and beads"
style="max-width:100%;height:auto;border-radius:10px;border:1px solid var(--line)"></p>
<h2>Questions</h2>{faq_html(faq)}"""
    urls.append(page("metrology/fiber-diameter/", "Fiber diameter analysis online from SEM images (electrospinning) | Jovian Labs",
                     "Measure nanofiber diameters from SEM images: length-weighted mean with 95% confidence interval, D10/D50/D90, "
                     "beads and alignment, measured like a CD-SEM line width. 1 USD per image, free demo.",
                     body, jsonld=[app_ld("Fiber Diameter Analyzer for SEM",
                                          "Fiber diameter distribution, beads and alignment from SEM images of fiber mats.",
                                          f"{SITE}/metrology/fiber-diameter/", APIFY_FI), faq_ld(faq)]))

    # ------------------------------------------------------------------ guide EN / FR
    alt = {"en": "metrology/eu-nanomaterial-definition/", "fr": "metrologie/definition-nanomateriau-ue/"}
    body = f"""<h1>The EU definition of nanomaterial, and how to screen a powder with electron microscopy</h1>
<p class="lede">A practical reading of Commission Recommendation 2022/C 229/01 of 10 June 2022, for R&amp;D and product stewardship
teams. Not legal advice: sector regulations (cosmetics, food, biocides, REACH) have their own texts and guidance.</p>
<h2>What the definition says</h2>
<p>A nanomaterial is a natural, incidental or manufactured material consisting of solid particles, on their own or as identifiable
constituent particles in aggregates or agglomerates, where <b>50% or more of the particles in the number-based size distribution</b>
meet at least one condition:</p>
<ul><li>(a) one or more external dimensions between 1 nm and 100 nm;</li>
<li>(b) an elongated shape (rod, fibre, tube) with two external dimensions below 1 nm and the other above 100 nm;</li>
<li>(c) a plate-like shape with one external dimension below 1 nm and the others above 100 nm.</li></ul>
<p>Particles with at least two orthogonal external dimensions above 100 µm need not be considered, and a material with a volume
specific surface area below 6 m²/cm³ is not a nanomaterial.</p>
<h2>Why electron microscopy</h2>
<p>The criterion counts particles by number and looks at their smallest dimension, including particles inside agglomerates.
Electron microscopy sees individual particles and their shape, which is why it is a reference method. On an image, the smallest
external dimension is approximated by the <b>minimum Feret diameter</b>, the smallest width of the particle's projection.</p>
<h2>Reading a screening result</h2>
<ul><li><b>Count enough particles.</b> The EU NanoDefine project recommends at least 500 for electron microscopy.</li>
<li><b>Look at the interval, not just the percentage.</b> A result of 55% with an interval from 44% to 66% does not settle the
question; a result of 95% with an interval from 91% to 98% does.</li>
<li><b>Know what pushes the number down.</b> Particles below the detection limit, particles hidden in agglomerates and platelets
lying flat (their thickness is not seen) all make a material look less “nano” than it is.</li></ul>
<div class="cta"><b>Screen your images</b><p class="small">The <a href="/metrology/particle-size/">particle size tool</a> reports
the share of particles at or below 100 nm, its uncertainty and a meets / not met / borderline verdict, with a PDF report.
1 USD per image, free demo.</p></div>
<p class="small">Version française : <a href="/metrologie/definition-nanomateriau-ue/">la définition européenne des nanomatériaux</a>.</p>"""
    urls.append(page(alt["en"], "EU nanomaterial definition (2022) explained, and how to screen with SEM/TEM | Jovian Labs",
                     "What Commission Recommendation 2022/C 229/01 says (50% of particles by number with a dimension of 1–100 nm), "
                     "why electron microscopy is used, and how to read a nanomaterial screening result.", body, alt=alt))
    body = f"""<h1>La définition européenne des nanomatériaux, et comment dépister une poudre au microscope électronique</h1>
<p class="lede">Une lecture pratique de la recommandation de la Commission 2022/C 229/01 du 10 juin 2022, pour les équipes R&amp;D
et réglementaires. Ce n'est pas un avis juridique : les réglementations sectorielles (cosmétiques, alimentation, biocides, REACH)
ont leurs propres textes.</p>
<h2>Ce que dit la définition</h2>
<p>Un nanomatériau est un matériau naturel, formé accidentellement ou manufacturé, constitué de particules solides, isolées ou
constitutives identifiables d'agrégats ou d'agglomérats, dont <b>50 % ou plus des particules, dans la distribution en nombre</b>,
remplissent au moins une condition :</p>
<ul><li>(a) une ou plusieurs dimensions externes comprises entre 1 et 100 nm ;</li>
<li>(b) une forme allongée (bâtonnet, fibre, tube) dont deux dimensions externes sont inférieures à 1 nm et l'autre supérieure à 100 nm ;</li>
<li>(c) une forme de plaquette dont une dimension externe est inférieure à 1 nm et les autres supérieures à 100 nm.</li></ul>
<p>Les particules dont au moins deux dimensions externes orthogonales dépassent 100 µm ne sont pas prises en compte, et un matériau
dont la surface spécifique en volume est inférieure à 6 m²/cm³ n'est pas un nanomatériau.</p>
<h2>Pourquoi la microscopie électronique</h2>
<p>Le critère compte les particules en nombre et regarde leur plus petite dimension, y compris dans les agglomérats. La microscopie
électronique voit les particules une à une et leur forme : c'est une méthode de référence. Sur une image, la plus petite dimension
externe est approchée par le <b>Feret minimal</b>, la plus petite largeur de la projection de la particule.</p>
<h2>Lire un résultat de dépistage</h2>
<ul><li><b>Compter assez de particules.</b> Le projet européen NanoDefine recommande au moins 500 particules en microscopie électronique.</li>
<li><b>Regarder l'intervalle, pas seulement le pourcentage.</b> 55 % avec un intervalle de 44 à 66 % ne tranche pas ; 95 % avec un
intervalle de 91 à 98 % tranche.</li>
<li><b>Savoir ce qui fait baisser le chiffre.</b> Les particules sous la limite de détection, celles cachées dans les agglomérats et
les plaquettes vues à plat (leur épaisseur n'est pas visible) font paraître un matériau moins « nano » qu'il ne l'est.</li></ul>
<div class="cta"><b>Dépister vos images</b><p class="small">L'<a href="/metrology/particle-size/">outil de granulométrie</a> donne la
part de particules ≤ 100 nm, son incertitude et un verdict « atteint / non atteint / proche du seuil », avec un rapport PDF en
français. 1 USD par image, démonstration gratuite.</p></div>
<p class="small">English version: <a href="/metrology/eu-nanomaterial-definition/">the EU nanomaterial definition explained</a>.</p>"""
    urls.append(page(alt["fr"], "Définition européenne des nanomatériaux (2022) : explication et dépistage au MEB/MET | Jovian Labs",
                     "Ce que dit la recommandation 2022/C 229/01 (50 % des particules en nombre avec une dimension de 1 à 100 nm), "
                     "pourquoi la microscopie électronique, et comment lire un résultat de dépistage.", body, lang="fr", alt=alt))

    today = dt.date.today().isoformat()
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (ROOT / "metrology" / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    return urls


if __name__ == "__main__":
    for u in build():
        print(u)
