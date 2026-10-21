"""Jovian Labs — free microscopy image analysis demo (one image per run).

This Space is a thin front end: the image is sent to the Jovian Labs Actors on Apify, which run the analysis and
return the PDF report, the control image and the statistics. The analysis code is not part of this Space.
"""
import datetime as dt
import io
import os
import secrets
import threading
import time
import urllib.request
from decimal import Decimal
from pathlib import Path

import gradio as gr
from apify_client import ApifyClient
from PIL import Image

TOKEN = os.environ.get("APIFY_TOKEN")
DAILY_CAP = int(os.environ.get("DAILY_CAP", "15"))
MAX_MB = 15
STORE = "hf-demo-uploads"
EX = Path(__file__).parent / "examples"
SITE = "https://jovianlabsstudio.github.io/metrology/"

TOOLS = {
    "particle": dict(actor="jovianlabs/sem-tem-particle-size", scale="scaleBarNm", px="pixelSizeNm", scale_int=True,
                     store="https://apify.com/jovianlabs/sem-tem-particle-size"),
    "porosity": dict(actor="jovianlabs/porosity-analyzer", scale="scaleBarUm", px="pixelSizeUm",
                     store="https://apify.com/jovianlabs/porosity-analyzer"),
    "fiber": dict(actor="jovianlabs/fiber-diameter-analyzer", scale="scaleBarNm", px="pixelSizeNm",
                  store="https://apify.com/jovianlabs/fiber-diameter-analyzer"),
}
CTYPE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".tif": "image/tiff", ".tiff": "image/tiff",
         ".bmp": "image/bmp"}

_lock = threading.Lock()
_count = {"day": None, "n": 0}


def _get(obj, *names):
    for n in names:
        if isinstance(obj, dict) and n in obj:
            return obj[n]
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def _take_slot():
    with _lock:
        today = dt.date.today().isoformat()
        if _count["day"] != today:
            _count.update(day=today, n=0)
        if _count["n"] >= DAILY_CAP:
            return False
        _count["n"] += 1
        return True


def _num(text):
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    float(text)  # raises ValueError if not a number
    return text


def _summary(tool, it):
    q = it.get("quality_status", "?")
    if tool == "particle":
        rows = [("Particles measured", it.get("particles")),
                ("D10 · D50 · D90", f"{it.get('d10_nm')} · {it.get('d50_nm')} · {it.get('d90_nm')} nm"),
                ("D50, 95 % confidence interval", it.get("d50_ci95")),
                ("EU nanomaterial criterion (a)", f"{it.get('eu_nano_verdict', '—')} · {it.get('eu_nano_fraction_pct', '—')} % "
                                                  f"of particles ≤ 100 nm (interval {it.get('eu_nano_interval', '—')})")]
    elif tool == "porosity":
        rows = [("Area porosity", it.get("porosity")),
                ("Pores", f"{it.get('pores')} ({it.get('pores_per_mm2')} per mm²)"),
                ("Pore D50 · largest pore", f"{it.get('pore_d50_um')} µm · {it.get('largest_pore_feret_um')} µm"),
                ("Share of porosity from irregular pores", f"{it.get('irregular_pores_share_pct')} %"),
                ("Threshold sensitivity", f"± {it.get('threshold_sensitivity_pct')} %")]
    else:
        rows = [("Fiber diameter", it.get("diameter")),
                ("Median · D10 · D90", f"{it.get('median_nm')} · {it.get('d10_nm')} · {it.get('d90_nm')} nm"),
                ("Fiber segments measured", it.get("segments")),
                ("Beads (lower bound)", it.get("beads_lower_bound")),
                ("Alignment index (0–1)", it.get("alignment_index"))]
    rows.append(("Quality checks", q))
    md = "| Result | Value |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows)
    md += f"\n\n**[Download the full PDF report]({it.get('report_url')})** · statistics with a single image are indicative: " \
          f"use 3 to 10 images per sample on [Apify]({TOOLS[tool]['store']}) for a reportable result."
    return md


def analyse(tool, file, scale, px, lang, progress=gr.Progress()):
    if not TOKEN:
        return "The demo is not configured yet. Please use the tool on Apify.", None
    if file is None:
        return "Upload an image first (or click one of the examples).", None
    path = Path(file if isinstance(file, str) else file.name)
    ext = path.suffix.lower()
    if ext not in CTYPE:
        return "Please upload a TIFF, PNG, JPG or BMP image.", None
    if path.stat().st_size > MAX_MB * 1024 * 1024:
        return f"The free demo accepts images up to {MAX_MB} MB.", None
    try:
        scale, px = _num(scale), _num(px)
    except ValueError:
        return "The scale bar length and the pixel size must be numbers.", None
    if not _take_slot():
        return (f"The free demo quota for today is used up. Run the tool directly on [Apify]({TOOLS[tool]['store']}) "
                "(demo runs there are free too) or come back tomorrow."), None

    cfg = TOOLS[tool]
    client = ApifyClient(TOKEN)
    progress(0.1, desc="Uploading the image")
    store = client.key_value_stores().get_or_create(name=STORE)
    kv = client.key_value_store(_get(store, "id"))
    key = f"u-{int(time.time())}-{secrets.token_hex(4)}{ext}"
    kv.set_record(key, path.read_bytes(), content_type=CTYPE[ext])
    try:
        url = kv.get_record_public_url(key)
        run_input = {"imageUrls": [url], "sampleName": "HF-DEMO", "reportLanguage": lang, "maxImages": 1}
        if scale:  # l'Actor granulométrie attend un entier, les autres une chaîne
            run_input[cfg["scale"]] = int(round(float(scale))) if cfg.get("scale_int") else scale
        if px:
            run_input[cfg["px"]] = px
        progress(0.3, desc="Analysing on Apify (about 30 to 60 seconds)")
        # plafond de dépense minuscule : la démo ne doit jamais déclencher la facturation à l'image
        run = client.actor(cfg["actor"]).call(run_input=run_input, memory_mbytes=2048,
                                              run_timeout=dt.timedelta(seconds=300),
                                              max_total_charge_usd=Decimal("0.01"))
    except Exception as e:  # noqa: BLE001
        print(f"[demo] {cfg['actor']} call failed: {e!r}", flush=True)
        return ("The analysis service could not be reached. Please try again later or run the tool on "
                f"[Apify]({cfg['store']})."), None
    finally:
        try:
            kv.delete_record(key)  # the uploaded image is not kept
        except Exception:
            pass
    charged = _get(run, "charged_event_counts", "chargedEventCounts")
    print(f"[demo] {cfg['actor']} run {_get(run, 'id')} status {_get(run, 'status')} charged {charged}", flush=True)
    status = str(_get(run, "status") or "")
    if "SUCCEEDED" not in status:
        msg = _get(run, "status_message", "statusMessage") or status
        return f"The analysis did not complete: {msg}", None
    items = _get(client.dataset(_get(run, "default_dataset_id", "defaultDatasetId")).list_items(), "items") or []
    if not items:
        return "The analysis returned no result.", None
    it = items[0]
    progress(0.9, desc="Fetching the control image")
    img = None
    try:
        with urllib.request.urlopen(it["control_sheet_url"], timeout=60) as r:
            img = Image.open(io.BytesIO(r.read())).convert("RGB")
    except Exception:
        pass
    return _summary(tool, it), img


def tab(tool, title, intro, file_label, scale_label, px_label, example, scale_example):
    with gr.Tab(title):
        gr.Markdown(intro)
        with gr.Row():
            with gr.Column(scale=1):
                f = gr.File(label=file_label, file_types=list(CTYPE), type="filepath")
                s = gr.Textbox(label=scale_label, placeholder="e.g. " + scale_example)
                p = gr.Textbox(label=px_label, placeholder="only if the image has no scale bar or metadata")
                lang = gr.Radio(["en", "fr"], value="en", label="Report language")
                b = gr.Button("Analyse (free, one image)", variant="primary")
                gr.Examples([[str(EX / example), scale_example]], inputs=[f, s], label="Synthetic example")
            with gr.Column(scale=1):
                out = gr.Markdown()
                im = gr.Image(label="Control image: what was measured", interactive=False)
        b.click(lambda *a: analyse(tool, *a), inputs=[f, s, p, lang], outputs=[out, im], concurrency_limit=1)


with gr.Blocks(title="Microscopy image analysis · Jovian Labs", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# Microscopy image analysis, with the uncertainty attached\n"
        "Upload **one** image and get the measurement, a control image and a full PDF report. Original Zeiss or "
        "Thermo Fisher TIFF files are calibrated automatically from their metadata; otherwise give the scale bar length. "
        f"For several images per sample, batch runs and the API, use the tools on Apify. More: [Jovian Labs metrology]({SITE})."
    )
    tab("particle", "Particle size & EU nano screening",
        "SEM/TEM images of powders or nanoparticles: D10/D50/D90 with confidence intervals and the share of particles at "
        "or below 100 nm (EU nanomaterial definition, criterion a).",
        "SEM/TEM image", "Scale bar length (nm)", "Pixel size (nm/px)", "synthetic_sem_particles_200nm-bar.png", "200")
    tab("porosity", "Porosity of cross-sections",
        "Polished, unetched cross-sections (optical or SEM) of AM parts, castings or coatings: area porosity, pore sizes, "
        "largest pores, round vs lack-of-fusion pores.",
        "Micrograph", "Scale bar length (µm)", "Pixel size (µm/px)", "synthetic_cross_section_100um-bar.png", "100")
    tab("fiber", "Fiber diameter",
        "SEM images of electrospun mats, filter media or nonwovens: length-weighted fiber diameter with confidence "
        "interval, beads and alignment.",
        "SEM image", "Scale bar length (nm)", "Pixel size (nm/px)", "synthetic_nanofibers_5um-bar.png", "5000")
    gr.Markdown(
        f"<small>Free demo: {DAILY_CAP} analyses per day for everyone, one image each. Images are sent to Apify for the "
        "analysis; the uploaded file is deleted right after the run, and run outputs are removed automatically by Apify "
        "after a few days. Automated image analysis, not an accredited (ISO/IEC 17025) measurement. "
        "Contact: jovianlabsstudio@gmail.com</small>"
    )

if __name__ == "__main__":
    demo.queue(max_size=10).launch()
