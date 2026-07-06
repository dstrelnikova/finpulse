from datetime import date

from fastapi import APIRouter, Response

from app.core.settings import settings

router = APIRouter(tags=["SEO"])


@router.get("/robots.txt", include_in_schema=False)
def robots_txt() -> Response:
    api_base = settings.API_BASE_URL.rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /news/public",
        "Allow: /market/moex",
        "",
        "Disallow: /admin",
        "Disallow: /chat",
        "Disallow: /profile",
        "Disallow: /news",
        "",
        f"Sitemap: {api_base}/sitemap.xml",
    ]
    return Response(content="\n".join(lines), media_type="text/plain; charset=utf-8")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml() -> Response:
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    today = date.today().isoformat()
    urls = [
        (f"{base}/", "daily", "1.0"),
        (f"{base}/news/public", "hourly", "0.9"),
        (f"{base}/market/moex", "hourly", "0.8"),
        (f"{base}/login", "monthly", "0.4"),
        (f"{base}/register", "monthly", "0.5"),
    ]

    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, changefreq, priority in urls:
        body.extend(
            [
                "  <url>",
                f"    <loc>{loc}</loc>",
                f"    <lastmod>{today}</lastmod>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    body.append("</urlset>")
    return Response(content="\n".join(body), media_type="application/xml; charset=utf-8")
