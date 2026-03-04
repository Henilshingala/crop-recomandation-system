import os, time
from huggingface_hub import HfApi

api = HfApi(token=os.environ.get("HF_TOKEN", ""))
for i in range(25):
    info = api.space_info("shingala/CRS")
    s = info.runtime.stage if info.runtime else "unknown"
    print(f"  [{i*10}s] {s}")
    if s == "RUNNING":
        print("READY!")
        break
    time.sleep(10)
else:
    print("Timed out")
