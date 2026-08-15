from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("demo_openamp.webui.webui:app", reload=True)
