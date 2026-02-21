"""Repository entrypoint for Hugging Face Spaces.

This wrapper loads the FastAPI app defined in Aiml/app.py.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

AIML_DIR = Path(__file__).resolve().parent / "Aiml"
AIML_APP = AIML_DIR / "app.py"

if not AIML_APP.exists():
    raise RuntimeError(f"Missing Aiml app at: {AIML_APP}")

# Ensure relative file loads inside Aiml/app.py work (joblib/csv paths, etc.).
os.chdir(str(AIML_DIR))

spec = importlib.util.spec_from_file_location("aiml_app", str(AIML_APP))
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load Aiml/app.py module")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
