from fastapi import FastAPI, Request
from pydantic import BaseModel
import aiohttp
import asyncio
import os
import subprocess
import uuid

app = FastAPI()

class MediaRequest(BaseModel):
    file_url: str

@app.post("/api/mediainfo")
async def get_mediainfo(data: MediaRequest):
    url = data.file_url
    filename = f"/tmp/{uuid.uuid4()}"
    try:
        # Download first 30MB
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Range": "bytes=0-30000000"}) as resp:
                if resp.status != 200 and resp.status != 206:
                    return {"error": f"Failed to download file: {resp.status}"}
                with open(filename, "wb") as f:
                    while True:
                        chunk = await resp.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

        # Run mediainfo
        result = subprocess.run(["mediainfo", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stderr:
            return {"error": result.stderr}
        return {"metadata": result.stdout}

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(filename):
            os.remove(filename)
