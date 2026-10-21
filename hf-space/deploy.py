"""Publie le dossier space/ sur Hugging Face comme Space statique (gratuit).

Lancé par .github/workflows/hf-space.yml avec le secret GitHub HF_TOKEN (saisi par le propriétaire).
La démo interactive (gradio-app/) demande un abonnement PRO de Hugging Face : SDK=gradio et APIFY_TOKEN pour la publier.
"""
import os
from pathlib import Path

from huggingface_hub import HfApi

REPO = os.environ.get("HF_SPACE", "jovianlabs/microscopy-image-analysis")
SDK = os.environ.get("HF_SDK", "static")
FOLDER = "space" if SDK == "static" else "gradio-app"
api = HfApi(token=os.environ["HF_TOKEN"])
try:
    who = api.whoami()
    print("account:", who.get("name"), "| type:", who.get("type"), "| email verified:", who.get("emailVerified"),
          "| plan:", who.get("isPro"), "| token role:", (who.get("auth") or {}).get("accessToken", {}).get("role"))
except Exception as e:  # noqa: BLE001
    print("whoami failed:", e)
try:
    api.create_repo(REPO, repo_type="space", space_sdk=SDK, exist_ok=True, private=False)
except Exception as e:  # noqa: BLE001
    resp = getattr(e, "response", None)
    print("create_repo refused:", getattr(resp, "status_code", "?"), getattr(resp, "text", "")[:800])
    raise SystemExit(1)
if SDK != "static":
    if os.environ.get("APIFY_TOKEN"):
        api.add_space_secret(REPO, "APIFY_TOKEN", os.environ["APIFY_TOKEN"])
    api.add_space_variable(REPO, "DAILY_CAP", os.environ.get("DAILY_CAP", "15"))
api.upload_folder(folder_path=str(Path(__file__).parent / FOLDER), repo_id=REPO, repo_type="space",
                  commit_message="Update from github.com/jovianlabsstudio/jovianlabsstudio.github.io")
print(f"https://huggingface.co/spaces/{REPO}")
