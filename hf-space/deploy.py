"""Publie le dossier space/ sur Hugging Face (Space Gradio) et y range le secret APIFY_TOKEN.

Lancé par .github/workflows/hf-space.yml avec les secrets GitHub HF_TOKEN et APIFY_TOKEN (saisis par le propriétaire).
"""
import os
from pathlib import Path

from huggingface_hub import HfApi

REPO = os.environ.get("HF_SPACE", "jovianlabs/microscopy-image-analysis")
api = HfApi(token=os.environ["HF_TOKEN"])
api.create_repo(REPO, repo_type="space", space_sdk="gradio", exist_ok=True, private=False)
if os.environ.get("APIFY_TOKEN"):
    api.add_space_secret(REPO, "APIFY_TOKEN", os.environ["APIFY_TOKEN"])
api.add_space_variable(REPO, "DAILY_CAP", os.environ.get("DAILY_CAP", "15"))
api.upload_folder(folder_path=str(Path(__file__).parent / "space"), repo_id=REPO, repo_type="space",
                  commit_message="Update from github.com/jovianlabsstudio/jovianlabsstudio.github.io")
print(f"https://huggingface.co/spaces/{REPO}")
