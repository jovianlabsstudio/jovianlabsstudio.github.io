"""python -m aiindex run [--mock] [--only plumbers/austin-tx]   |   python -m aiindex render [--mock] [--out DIR]"""
import argparse
import json
from pathlib import Path

from . import measure, render

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "render", "all"])
    ap.add_argument("--mock", action="store_true", help="moteur simulé, sans API")
    ap.add_argument("--only", nargs="*", help="limiter à categorie/ville")
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "site"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config.json").read_text())
    if a.cmd in ("run", "all"):
        measure.run(cfg, mock=a.mock, out_dir=a.data, only=a.only)
    if a.cmd in ("render", "all"):
        render.build(cfg, Path(a.data), Path(a.out), mock=a.mock)


if __name__ == "__main__":
    main()
