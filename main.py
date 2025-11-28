from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="JSON to Pydantic Converter",
    description="Convert JSON data to Pydantic models",
)

# Configuration
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Static directory might not exist yet
    pass


# SEO-friendly routes
@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots_txt():
    """Serve robots.txt file for search engines"""
    robots_path = os.path.join("static", "robots.txt")
    if os.path.exists(robots_path):
        with open(robots_path, "r") as f:
            return f.read()
    return "User-agent: *\nAllow: /\n"


@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def get_sitemap():
    """Serve sitemap.xml file for search engines"""
    sitemap_path = os.path.join("static", "sitemap.xml")
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r") as f:
            content = f.read()
        return PlainTextResponse(content=content, media_type="application/xml")

    # Generate simple sitemap if file doesn't exist
    return PlainTextResponse(
        content=(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "  <url>\n"
            "    <loc>https://json-to-pydantic.malachibazar.com/</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>1.0</priority>\n"
            "  </url>\n"
            "</urlset>"
        ),
        media_type="application/xml",
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "google_analytics_id": GOOGLE_ANALYTICS_ID,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
