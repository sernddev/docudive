import os

from fastapi import HTTPException, Request, Response, APIRouter
from fastapi.responses import FileResponse
from datetime import datetime
from hashlib import md5
from danswer.utils.logger import setup_logger
from danswer.configs.app_configs import ICON_DIRECTORY

logger = setup_logger()
basic_router = APIRouter(prefix="/icons")

# Supported image types
SUPPORTED_EXTENSIONS = {".png", ".svg", ".jpeg", ".jpg"}

@basic_router.get("/{file_path:path}")
async def serve_icon(file_path: str, request: Request, response: Response):
    # Build the full path (including subfolders)
    icon_path = os.path.join(ICON_DIRECTORY, file_path)

    # Check file extension is supported
    if not os.path.exists(icon_path):
        raise HTTPException(status_code=404, detail="Icon not found")

    file_extension = os.path.splitext(file_path)[-1].lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Get the last modified time of the file
    last_modified = os.path.getmtime(icon_path)
    last_modified_datetime = datetime.utcfromtimestamp(last_modified)
    last_modified_str = last_modified_datetime.strftime('%a, %d %b %Y %H:%M:%S GMT')

    with open(icon_path, "rb") as file:
        file_content = file.read()
        etag = md5(file_content).hexdigest()

    response.headers["Cache-Control"] = "public, max-age=3600"  # Cache for 1 hour
    response.headers["ETag"] = etag
    response.headers["Last-Modified"] = last_modified_str

    if_none_match = request.headers.get("If-None-Match")
    if_modified_since = request.headers.get("If-Modified-Since")

    if if_none_match == etag or (if_modified_since and if_modified_since == last_modified_str):
        response.status_code = 304
        return

    content_type = None
    if file_extension == ".png":
        content_type = "image/png"
    elif file_extension == ".svg":
        content_type = "image/svg+xml"
    elif file_extension in {".jpeg", ".jpg"}:
        content_type = "image/jpeg"

    return FileResponse(icon_path, media_type=content_type)