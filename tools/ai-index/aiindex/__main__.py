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
                js = e.complete_json('Reply only with this JSON object: {"ok": true, "businesses": ["A", "B"]}')
                print(f"{e.name} without web search: OK, parsed {js}")
            except E.EngineError as ex:
                print(f"{e.name} without web search: FAILED {ex}")
        try:
            ans = e.ask(q)
            print(f"{e.name} with web search: OK, {len(ans['text'])} characters, {len(ans['sources'])} sources")
            print(f"  endpoint: {getattr(e, 'last_endpoint', '?')}  response keys: {getattr(e, 'last_raw_keys', '?')}")
            if getattr(e, "last_error", None):
                print(f"  first endpoint error: {e.last_error}")
            for u in ans["sources"][:8]:
                print(f"  source: {u}")
            for path, u, ctx in list(E.url_paths(getattr(e, "last_raw", {})))[:15]:
                print(f"  link {path}: {u} {ctx}")
            print("  answer: " + ans["text"][:400].replace("\n", " / "))
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
