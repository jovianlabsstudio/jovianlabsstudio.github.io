---
title: Microscopy Image Analysis (interactive, needs HF PRO)
emoji: 🔬
colorFrom: indigo
colorTo: yellow
sdk: gradio
sdk_version: 5.50.0
python_version: "3.12"
app_file: app.py
pinned: false
license: other
short_description: Particle size, EU nano check, porosity, fiber diameter
---

# Microscopy image analysis, with the uncertainty attached

Free demo of the Jovian Labs microscopy tools. Upload one image and get the measurement, a control image and a PDF report:

- **Particle size & EU nanomaterial screening** (SEM/TEM): D10/D50/D90 with 95 % confidence intervals and the share of particles at or below 100 nm.
- **Porosity of polished cross-sections** (optical or SEM): area porosity, pore sizes, largest pores, round vs lack-of-fusion pores.
- **Fiber diameter** (SEM, electrospinning and filters): length-weighted diameter with confidence interval, beads and alignment.

This Space is a front end: the analysis runs on [Apify](https://apify.com/jovianlabs), where the same tools take several images per sample, run in batch and through an API (1 USD per image, demo runs free).

More information and example reports: https://jovianlabsstudio.github.io/metrology/
