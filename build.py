#!/usr/bin/env python3
"""Dimensure static site builder.

Each page lives in src/pages/<slug>.html and starts with a JSON header:

<!--META
{ "title": "...", "description": "...", "crumbs": [["Services","services.html"]],
  "schema": ["service"], "service": {...}, "faqs": [["Q","A"], ...], "image": "hero-..." }
-->
...page body HTML...

The builder wraps every page in the shared head, header, footer and
structured data, then writes site/, sitemap.xml, robots.txt and llms.txt.
"""
import json, re, os, shutil, html, datetime, pathlib

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "site"

SITE = {
    "name": "Dimensure",
    "url": "https://dimensure.co.uk",
    "email": "info@dimensure.co.uk",
    "tagline": "Measured. Checked. Recorded.",
    "base": "Corby, Northamptonshire",
}
TODAY = datetime.date.today().isoformat()

SERVICES = [
    # slug, short name, card blurb, image, cost page
    ("road-level-surveys.html", "Road & sub-base level surveys",
     "Sub-base and binder checked against the road design before the next layer goes on.",
     "road-subbase-scan", "road-level-survey-cost.html"),
    ("tarmac-depth-surveys.html", "Tarmac depth surveys",
     "Before-and-after scans that map the thickness actually laid, across the whole road.",
     "road-tarmac-scan", "tarmac-depth-survey-cost.html"),
    ("plot-oversite-surveys.html", "Plot & oversite surveys",
     "Slab flatness, brickwork to drawing and drain collar positions, checked plot by plot.",
     "hero-scanner-oversite", "plot-survey-cost.html"),
    ("as-built-surveys.html", "As-built surveys",
     "Finished roads, kerbs, drainage covers and plots recorded, with as-built drawings in DWG and PDF.",
     "as-built-survey", "as-built-survey-cost.html"),
    ("floor-flatness-surveys.html", "Floor flatness surveys",
     "Slabs and screeds scanned edge to edge and checked against SR1-SR3 or your flatness class.",
     "floor-flatness", "floor-flatness-survey-cost.html"),
    ("measured-building-surveys.html", "3D measured building surveys",
     "Millimetre-accurate floor plans and elevations for kitchens, extensions and architects.",
     "interior-scan", "measured-building-survey-cost.html"),
    ("topographical-surveys.html", "Topographical surveys",
     "Levels, contours, boundaries, buildings and trees for planning and design, with the full 3D scan.",
     "topographical-survey", "topographical-survey-cost.html"),
    ("groundworks-design-audit.html", "Dimensure Design Audit",
     "Groundworks and civils drawings reviewed before you dig, on any project: problems found on paper.",
     "design-audit", "groundworks-design-audit-cost.html"),
    ("garden-surveys.html", "Garden surveys",
     "Levels, walls, steps, trees and drains surveyed for garden designers, landscapers and homeowners.",
     "garden-scan", "garden-survey-cost.html"),
    ("drone-surveys.html", "Drone surveys",
     "Aerial mapping tied to RTK GNSS control: scaled orthophotos, levels and contours for whole sites.",
     "drone-survey", "drone-survey-cost.html"),
    ("stockpile-volume-surveys.html", "Stockpile volume surveys",
     "Every heap of stone, topsoil and spoil measured by drone, in cubic metres and tonnes.",
     "stockpile-survey", "stockpile-survey-cost.html"),
    ("earthworks-volume-surveys.html", "Earthworks volume surveys",
     "Cut and fill against design or a previous survey, topsoil strip depths and muck-shift checks.",
     "earthworks-survey", "earthworks-survey-cost.html"),
    ("site-progress-surveys.html", "Site progress surveys",
     "Monthly drone records of the whole site, compared with last month, for valuations and reports.",
     "site-progress", "site-progress-survey-cost.html"),
    ("setting-out.html", "GNSS setting out",
     "Site control on Ordnance Survey grid, and pegs for earthworks, drainage, roads and plots.",
     "gnss-setting-out", "setting-out-cost.html"),
    ("as-laid-service-surveys.html", "As-laid service surveys",
     "Drainage, chambers and ducts recorded in the open trench, with levels and photos, before backfill.",
     "as-laid-survey", "as-laid-survey-cost.html"),
    ("condition-surveys.html", "Pre-start condition surveys",
     "Roads, kerbs, walls and neighbouring buildings recorded by scan, drone and photo before work starts.",
     "condition-survey", "condition-survey-cost.html"),
    ("drone-roof-surveys.html", "Drone roof surveys",
     "Close-up roof inspections without scaffold, with measured roof areas and pitches if needed.",
     "roof-survey", "roof-survey-cost.html"),
    ("survey-data-reporting.html", "Reporting from your survey data",
     "Already have a scan or your engineer's levels? We process your data and report against design, no visit needed.",
     "report-tablet", None),
]

COST_LABEL = {
    "road-level-survey-cost.html": "Road level survey cost",
    "tarmac-depth-survey-cost.html": "Tarmac depth survey cost",
    "plot-survey-cost.html": "Plot survey cost",
    "measured-building-survey-cost.html": "Measured building survey cost",
    "garden-survey-cost.html": "Garden survey cost",
    "topographical-survey-cost.html": "Topographical survey cost",
    "as-built-survey-cost.html": "As-built survey cost",
    "floor-flatness-survey-cost.html": "Floor flatness survey cost",
    "groundworks-design-audit-cost.html": "Design audit cost",
    "drone-survey-cost.html": "Drone survey cost",
    "stockpile-survey-cost.html": "Stockpile survey cost",
    "earthworks-survey-cost.html": "Earthworks survey cost",
    "site-progress-survey-cost.html": "Progress survey cost",
    "setting-out-cost.html": "Setting out cost",
    "as-laid-survey-cost.html": "As-laid survey cost",
    "condition-survey-cost.html": "Condition survey cost",
    "roof-survey-cost.html": "Roof survey cost",
}

AREAS = [
    ("surveys-corby-kettering.html", "Corby & Kettering"),
    ("surveys-northampton.html", "Northampton"),
    ("surveys-milton-keynes.html", "Milton Keynes"),
    ("surveys-leicester.html", "Leicester & Leicestershire"),
    ("surveys-peterborough-stamford.html", "Peterborough & Stamford"),
    ("surveys-rutland.html", "Rutland"),
]

AREA_SERVED = ["Corby", "Kettering", "Wellingborough", "Northampton", "Milton Keynes",
               "Leicester", "Market Harborough", "Peterborough", "Stamford", "Oakham",
               "Uppingham", "Northamptonshire", "Leicestershire", "Rutland",
               "Buckinghamshire", "Cambridgeshire", "Lincolnshire", "Coventry", "Nottingham",
               "Bedford", "Cambridge", "East Midlands", "West Midlands", "United Kingdom"]

FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap" rel="stylesheet">')

LOGO = ('<span class="logo" aria-hidden="true"><span class="logo-a">DIMEN</span>'
        '<span class="logo-s"><i></i>S</span><span class="logo-b">URE</span></span>')


def esc(s):
    return html.escape(s, quote=True)


def img(name, alt, cls="", eager=False, sizes="(max-width: 800px) 100vw, 50vw"):
    """Responsive image tag for images/<name>-768.webp / -1536.webp."""
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="images/{name}-1536.webp" '
            f'srcset="images/{name}-768.webp 768w, images/{name}-1536.webp 1536w" '
            f'sizes="{sizes}" width="1536" height="1024" alt="{esc(alt)}" {load}>')


def service_cards(exclude=None, heading_level="h3"):
    out = ['<div class="cards">']
    for slug, name, blurb, image, cost in SERVICES:
        if slug == exclude:
            continue
        out.append(
            f'<article class="card"><a class="card-img" href="{slug}" tabindex="-1" aria-hidden="true">'
            f'{img(image, name + " - Dimensure laser scan surveys", sizes="(max-width: 700px) 100vw, 33vw")}</a>'
            f'<div class="card-body"><{heading_level}><a href="{slug}">{name}</a></{heading_level}>'
            f'<p>{blurb}</p><p class="card-links"><a href="{slug}">How it works</a>'
            + (f'<a href="{cost}">Prices</a>' if cost else '<a href="contact.html">Get a price</a>')
            + '</p></div></article>')
    out.append('</div>')
    return "".join(out)


def area_links(current=None):
    return '<ul class="pill-list">' + "".join(
        f'<li><a href="{s}">{n}</a></li>' for s, n in AREAS if s != current) + '</ul>'


def cost_links():
    return '<ul class="pill-list">' + "".join(
        f'<li><a href="{c}">{COST_LABEL[c]}</a></li>' for *_, c in SERVICES if c) + '</ul>'


MACROS = {
    "{{SERVICE_CARDS}}": lambda meta: service_cards(meta.get("exclude_card")),
    "{{ALL_SERVICE_CARDS}}": lambda meta: service_cards(),
    "{{AREA_LINKS}}": lambda meta: area_links(meta.get("_slug")),
    "{{COST_LINKS}}": lambda meta: cost_links(),
    "{{EMAIL}}": lambda meta: f'<a href="mailto:{SITE["email"]}">{SITE["email"]}</a>',
    "{{CTA}}": lambda meta: cta_block(meta),
    "{{SAMPLE_VIEWER}}": lambda meta: viewer_block(meta.get("viewer", "road")),
    "{{EMAIL_TEXT}}": lambda meta: SITE["email"],
}


def cta_block(meta):
    t = meta.get("cta_title", "Book a scan or ask a question")
    return (f'<section class="cta"><div class="wrap cta-in"><div><h2>{t}</h2>'
            f'<p>Send the drawing, the location and when you need it. We reply the same working day with a fixed price.</p></div>'
            f'<div class="cta-actions"><a class="btn" href="contact.html">Get a fixed price</a>'
            f'<a class="btn ghost" href="mailto:{SITE["email"]}">Email {SITE["email"]}</a></div></div></section>')


def viewer_block(kind):
    labels = {"road": "Sample scan: estate road sub-base against design levels",
              "slab": "Sample scan: oversite slab flatness",
              "garden": "Sample scan: rear garden levels",
              "room": "Sample scan: kitchen and extension shell"}
    return (f'<figure class="viewer" data-kind="{kind}">'
            f'<canvas aria-label="{esc(labels[kind])}. Drag to rotate." role="img"></canvas>'
            f'<div class="viewer-ui"><span class="viewer-tag">Sample data</span>'
            f'<div class="viewer-tabs" role="group" aria-label="Choose a sample scan">'
            f'<button type="button" data-k="road">Road</button><button type="button" data-k="slab">Slab</button>'
            f'<button type="button" data-k="garden">Garden</button><button type="button" data-k="room">Room</button></div></div>'
            f'<div class="viewer-legend" aria-hidden="true"><span>-15mm</span><b></b><span>+15mm</span></div>'
            f'<figcaption>{esc(labels[kind])}. Drag to rotate, scroll or pinch to zoom. Illustrative point cloud, not a client survey.</figcaption></figure>')


def nav(active):
    items = [("services.html", "Services"), ("prices.html", "Prices"), ("case-studies.html", "Case studies"), ("areas.html", "Areas"),
             ("how-it-works.html", "How it works"), ("about.html", "About"), ("faq.html", "FAQ")]
    li = []
    for href, label in items:
        cur = ' aria-current="page"' if href == active else ""
        if href == "services.html":
            sub = "".join(f'<li><a href="{s}">{n}</a></li>' for s, n, *_ in SERVICES)
            li.append(f'<li class="has-sub"><a href="{href}"{cur}>{label}</a><ul class="sub">{sub}</ul></li>')
        else:
            li.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    return "".join(li)


def header(active):
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap head-in">
<a class="brand" href="index.html" aria-label="Dimensure home">{LOGO}</a>
<input type="checkbox" id="nav-toggle" class="nav-toggle" aria-label="Open menu">
<label for="nav-toggle" class="nav-btn" aria-hidden="true"><span></span><span></span><span></span></label>
<nav class="nav" aria-label="Main"><ul>{nav(active)}<li><a href="https://app.dimensure.co.uk/login" rel="nofollow">Client login</a></li></ul>
<a class="btn small" href="contact.html">Get a price</a></nav>
</div></header>'''


def footer():
    svc = "".join(f'<li><a href="{s}">{n}</a></li>' for s, n, *_ in SERVICES)
    cst = "".join(f'<li><a href="{c}">{COST_LABEL[c]}</a></li>' for *_, c in SERVICES if c)
    ars = "".join(f'<li><a href="{s}">Surveys in {n}</a></li>' for s, n in AREAS)
    return f'''<footer class="site-footer"><div class="wrap">
<div class="foot-top"><a class="brand" href="index.html" aria-label="Dimensure home">{LOGO}</a>
<p class="foot-tag">{SITE["tagline"]}</p></div>
<div class="foot-grid">
<div><h2>Services</h2><ul>{svc}<li><a href="services.html">All services</a></li></ul></div>
<div><h2>Prices</h2><ul>{cst}<li><a href="prices.html">Price guide</a></li></ul></div>
<div><h2>Areas</h2><ul>{ars}<li><a href="areas.html">All areas</a></li></ul></div>
<div><h2>Contact</h2><ul class="nap">
<li><a href="mailto:{SITE["email"]}">{SITE["email"]}</a></li>
<li>Based in {SITE["base"]}</li>
<li><a href="case-studies.html">Case studies</a></li><li><a href="how-it-works.html">How it works</a></li><li><a href="about.html">About Dimensure</a></li>
<li><a href="faq.html">FAQ</a></li><li><a href="privacy.html">Privacy</a></li></ul></div>
</div>
<p class="legal">&copy; {datetime.date.today().year} Dimensure. Laser scan, drone and GNSS surveys: measured building, topographical, volume, setting out and construction QC surveys across the Midlands and the UK.</p>
</div></footer>
<a class="mobile-bar" href="contact.html">Get a fixed price</a>'''


def org_schema():
    return {
        "@type": "ProfessionalService",
        "@id": SITE["url"] + "/#business",
        "name": SITE["name"],
        "url": SITE["url"] + "/",
        "email": SITE["email"],
        "logo": SITE["url"] + "/images/dimensure-logo.png",
        "image": SITE["url"] + "/images/hero-scanner-oversite-1536.webp",
        "slogan": SITE["tagline"],
        "description": ("Laser scan survey company: measured building surveys, topographical and garden level surveys, "
                        "road and sub-base level surveys, tarmac depth surveys, plot and oversite as-built surveys "
                        "groundworks design audits, drone surveys, stockpile and earthworks volume surveys, construction progress surveys, "
                        "RTK GNSS setting out, as-laid drainage and duct records, pre-start condition surveys and drone roof surveys, "
                        "plus QC reporting from survey data supplied by the client's own engineer."),
        "address": {"@type": "PostalAddress", "addressLocality": "Corby",
                    "addressRegion": "Northamptonshire", "addressCountry": "GB"},
        "areaServed": [{"@type": "Place", "name": a} for a in AREA_SERVED],
        "knowsAbout": ["Groundworks design review", "Terrestrial laser scanning", "Point cloud surveys", "Sub-base level checks",
                       "Asphalt layer thickness verification", "Slab flatness surveys",
                       "Measured building surveys", "Topographical surveys", "Garden level surveys", "As-built surveys", "Laser scan surveys", "3D laser scanning", "Groundworks quality control",
                       "Point cloud processing", "Survey data QC reporting",
                       "Drone surveys", "Aerial photogrammetry", "Orthophotos", "Stockpile volume measurement",
                       "Cut and fill earthworks surveys", "Construction progress monitoring", "RTK GNSS surveying",
                       "Construction setting out", "As-laid drainage records", "Schedules of condition", "Drone roof inspections"],
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                                      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                      "opens": "07:30", "closes": "17:30"},
        "priceRange": "££",
    }


def build_schema(meta, slug):
    url = SITE["url"] + "/" + ("" if slug == "index.html" else slug)
    graph = [org_schema()]
    page = {"@type": meta.get("page_type", "WebPage"), "@id": url + "#webpage", "url": url,
            "name": meta["title"], "description": meta["description"],
            "isPartOf": {"@id": SITE["url"] + "/#website"}, "about": {"@id": SITE["url"] + "/#business"},
            "dateModified": TODAY, "inLanguage": "en-GB"}
    if meta.get("image"):
        page["primaryImageOfPage"] = SITE["url"] + f"/images/{meta['image']}-1536.webp"
    graph.append(page)
    if slug == "index.html":
        graph.append({"@type": "WebSite", "@id": SITE["url"] + "/#website", "url": SITE["url"] + "/",
                      "name": "Dimensure", "inLanguage": "en-GB", "publisher": {"@id": SITE["url"] + "/#business"}})
    crumbs = [["Home", "index.html"]] + meta.get("crumbs", [])
    if slug != "index.html":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": SITE["url"] + "/" + ("" if h == "index.html" else h)} for i, (n, h) in enumerate(crumbs)]})
    if meta.get("service"):
        s = meta["service"]
        svc = {"@type": "Service", "name": s["name"], "serviceType": s.get("type", s["name"]),
               "description": s["description"], "provider": {"@id": SITE["url"] + "/#business"},
               "areaServed": [{"@type": "Place", "name": a} for a in s.get("areas", AREA_SERVED)],
               "url": url}
        if s.get("price_from"):
            svc["offers"] = {"@type": "Offer", "priceCurrency": "GBP",
                             "priceSpecification": {"@type": "PriceSpecification", "minPrice": s["price_from"],
                                                    "priceCurrency": "GBP"},
                             "url": SITE["url"] + "/" + s.get("price_page", slug)}
        graph.append(svc)
    if meta.get("faqs"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}}
            for q, a in meta["faqs"]]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def crumbs_html(meta):
    c = meta.get("crumbs")
    if not c:
        return ""
    parts = ['<li><a href="index.html">Home</a></li>']
    for i, (n, h) in enumerate(c):
        if i == len(c) - 1:
            parts.append(f'<li aria-current="page">{n}</li>')
        else:
            parts.append(f'<li><a href="{h}">{n}</a></li>')
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{"".join(parts)}</ol></nav>'


def faq_html(meta):
    if not meta.get("faqs"):
        return ""
    items = "".join(f'<details><summary><h3>{q}</h3></summary><div class="ans"><p>{a}</p></div></details>'
                    for q, a in meta["faqs"])
    title = meta.get("faq_title", "Questions we get asked")
    return f'<section class="section faq"><div class="wrap narrow"><h2>{title}</h2>{items}</div></section>'


def page(slug, meta, body):
    url = SITE["url"] + "/" + ("" if slug == "index.html" else slug)
    og = SITE["url"] + f"/images/{meta.get('image', 'hero-scanner-oversite')}-1536.webp"
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else \
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">'
    for k, fn in MACROS.items():
        if k in body:
            body = body.replace(k, fn(meta))
    body = re.sub(r"\{\{IMG:([^|}]+)\|([^|}]+)(?:\|(eager))?\}\}",
                  lambda m: img(m.group(1), m.group(2), eager=bool(m.group(3))), body)
    viewer_js = '<script src="assets/scan-viewer.js" defer></script>' if 'class="viewer"' in body else ""
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta["title"])}</title>
<meta name="description" content="{esc(meta["description"])}">
{robots}
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#071820">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Dimensure">
<meta property="og:locale" content="en_GB">
<meta property="og:title" content="{esc(meta.get("og_title", meta["title"]))}">
<meta property="og:description" content="{esc(meta["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1536"><meta property="og:image:height" content="1024">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
{FONT_LINK}
<link rel="stylesheet" href="assets/site.css">
<script type="application/ld+json">{build_schema(meta, slug)}</script>
</head>
<body class="{meta.get("body_class", "")}">
{header(meta.get("nav", slug))}
{crumbs_html(meta)}
<main id="main">
{body}
{faq_html(meta)}
{cta_block(meta) if not meta.get("no_cta") else ""}
</main>
{footer()}
{viewer_js}
</body>
</html>
'''


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SRC / "assets", OUT / "assets")
    shutil.copytree(ROOT / "images", OUT / "images")
    if (SRC / "downloads").exists():
        shutil.copytree(SRC / "downloads", OUT / "downloads")
    for f in (SRC / "static").iterdir():
        shutil.copy(f, OUT / f.name)
    urls = []
    llms_pages = []
    for p in sorted((SRC / "pages").glob("*.html")):
        raw = p.read_text()
        m = re.match(r"<!--META\s*(\{.*?\})\s*-->\s*", raw, re.S)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        slug = p.name
        meta["_slug"] = slug
        (OUT / slug).write_text(page(slug, meta, body))
        if not meta.get("noindex"):
            urls.append((slug, meta.get("priority", "0.7")))
            llms_pages.append((slug, meta["title"], meta["description"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for slug, pr in sorted(urls, key=lambda x: (x[0] != "index.html", x[0])):
        loc = SITE["url"] + "/" + ("" if slug == "index.html" else slug)
        sm.append(f"<url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm))
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# AI search and answer engines are welcome to read and cite this site\n"
        "User-agent: GPTBot\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\n"
        "User-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\n"
        "User-agent: Google-Extended\nAllow: /\n\nUser-agent: Applebot-Extended\nAllow: /\n\n"
        f"Sitemap: {SITE['url']}/sitemap.xml\n")
    llms = (SRC / "llms-intro.md").read_text().replace("{{EMAIL}}", SITE["email"])
    groups = [("Services", [s for s, *_ in SERVICES] + ["services.html"]),
              ("Prices", [c for *_, c in SERVICES if c] + ["prices.html"]),
              ("Areas", [s for s, _ in AREAS] + ["areas.html"]),
              ("Case studies", ["case-studies.html", "case-study-missing-road-gullies.html", "case-study-tarmac-thickness.html"])]
    used = set()
    for title, slugs in groups:
        llms += f"\n## {title}\n\n"
        for s in slugs:
            for slug, t, d in llms_pages:
                if slug == s:
                    llms += f"- [{t}]({SITE['url']}/{slug}): {d}\n"
                    used.add(slug)
    llms += "\n## Company\n\n"
    for slug, t, d in llms_pages:
        if slug not in used:
            u = SITE["url"] + "/" + ("" if slug == "index.html" else slug)
            llms += f"- [{t}]({u}): {d}\n"
    (OUT / "llms.txt").write_text(llms)
    print(f"Built {len(urls)} indexable pages")


if __name__ == "__main__":
    main()
