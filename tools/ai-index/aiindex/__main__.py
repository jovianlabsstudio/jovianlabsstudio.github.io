"""python -m aiindex run [--mock] [--only plumbers/austin-tx]  |  render [--mock] [--out DIR]  |  probe (diagnostic des clés, 2 appels par moteur)"""
import argparse
import json
from pathlib import Path

from . import measure, render

ROOT = Path(__file__).resolve().parents[1]


def probe(cfg):
    """Vérifie chaque clé avec 2 appels : sans recherche web, puis avec. N'écrit rien."""
    from . import engines as E
    q = "Who is the best plumber in Austin, TX? Answer in one sentence."
    for e in E.make(cfg["engines"], skip_missing=True):
        if hasattr(e, "complete_json"):
            try:
                e.complete_json('Reply with the JSON {"ok": true}')
                print(f"{e.name} without web search: OK")
            except E.EngineError as ex:
                print(f"{e.name} without web search: FAILED {ex}")
        try:
            ans = e.ask(q)
            print(f"{e.name} with web search: OK, {len(ans['text'])} characters, {len(ans['sources'])} sources")
        except E.EngineError as ex:
            print(f"{e.name} with web search: FAILED {ex}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "render", "all", "probe"])
    ap.add_argument("--mock", action="store_true", help="moteur simulé, sans API")
    ap.add_argument("--only", nargs="*", help="limiter à categorie/ville")
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", default=str(ROOT / "site"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "config.json").read_text())
    if a.cmd == "probe":
        probe(cfg)
        return
    if a.cmd in ("run", "all"):
        measure.run(cfg, mock=a.mock, out_dir=a.data, only=a.only)
    if a.cmd in ("render", "all"):
        render.build(cfg, Path(a.data), Path(a.out), mock=a.mock)


if __name__ == "__main__":
    main()
