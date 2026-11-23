# -*- coding: utf-8 -*-
"""Re-dress finished Dimensure PDFs (no HTML source) in the 2026 document format (brand2.py):
new cover page, navy header bar with the brand-kit logo, two-line footer and page numbers.

Per page: the old header (DIMENSURE wordmark, right-hand ref text, rule) and old footer are
removed (redacted), then the remaining content is moved (and only if needed, scaled uniformly) into
the brand2 body area so nothing sits under the new header bar or footer. Content itself is
not altered.

usage: python3 rebrand_demo.py <in.pdf> <out.pdf> <job.json>
"""
import io, json, sys, os
import pdfplumber
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
import brand2  # noqa: E402

TOP_LIMIT = 62.0      # content starts at least this far below the page top (bar is 40.6)
BOTTOM_LIMIT = 52.0   # content ends at least this far above the page bottom (footer rule 42.6)
FOOTER_ZONE = 30.0    # old footer text sits ~16pt from the bottom


def old_header_bottom(pg):
    """y (from top) just below the old header rule, or None if this page has no old header."""
    words = pg.extract_words()
    if not any(w["text"] == "DIMENSURE" and w["top"] < 60 for w in words):
        return None
    rules = [r for r in (pg.lines + pg.rects) if r["top"] < 95 and r["width"] > 300 and r["height"] < 3]
    return (max(r["bottom"] for r in rules) if rules else 80.0) + 1.5


def content_box(pg, head_cut):
    H = pg.height
    tops, bots = [], []
    objs = pg.chars + pg.lines + pg.rects + pg.curves + pg.images
    for o in objs:
        if o.get("width", 0) > pg.width - 10 and o.get("height", 0) > H - 10:
            continue  # page background
        if head_cut is not None and o["bottom"] <= head_cut + 0.5:
            continue
        if o["top"] >= H - FOOTER_ZONE:
            continue
        tops.append(o["top"]); bots.append(o["bottom"])
    return min(tops), max(bots)


def mask_page(W, H, head_cut):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H))
    c.setFillColor("#FFFFFF")
    if head_cut is not None:
        c.rect(0, H - head_cut, W, head_cut, stroke=0, fill=1)
    c.rect(0, 0, W, FOOTER_ZONE, stroke=0, fill=1)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]


def strip_old(src, cleaned):
    """Truly remove (redact) the old header and footer, text and line art, so no hidden old
    page numbers or headers stay in the text layer. Returns the old-header cut per page."""
    import pymupdf
    cuts = []
    with pdfplumber.open(src) as p:
        for pg in p.pages:
            cuts.append(old_header_bottom(pg))
    doc = pymupdf.open(src)
    for page, cut in zip(doc, cuts):
        r = page.rect
        if cut is not None:
            page.add_redact_annot(pymupdf.Rect(0, 0, r.width, cut), fill=False)
        page.add_redact_annot(pymupdf.Rect(0, r.height - FOOTER_ZONE, r.width, r.height), fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    doc.save(cleaned, garbage=3, deflate=True)
    return cuts


def rebrand(src, out, job):
    cleaned = out + ".clean.tmp.pdf"
    cuts = strip_old(src, cleaned)
    reader = PdfReader(cleaned)
    plumb = pdfplumber.open(cleaned)
    tmp_cover = out + ".cover.tmp.pdf"
    brand2._pdf(brand2.cover_html(dict(job["cover"], foot=job["foot"])), tmp_cover,
                {"top": "0", "bottom": "0", "left": "0", "right": "0"})
    w = PdfWriter()
    w.add_page(PdfReader(tmp_cover).pages[0])
    total = 1 + len(reader.pages)
    log = []
    for i, (page, pp) in enumerate(zip(reader.pages, plumb.pages), start=2):
        W, H = float(page.mediabox.width), float(page.mediabox.height)
        head_cut = cuts[i - 2]
        ct, cb = content_box(pp, head_cut)
        avail = (H - BOTTOM_LIMIT) - TOP_LIMIT
        s = min(1.0, avail / (cb - ct))
        # place content top at TOP_LIMIT (from top); scale about the page's horizontal centre
        new_top = TOP_LIMIT
        # PDF y-up: a point at distance d from top has y = H - d
        ty = (H - new_top) - s * (H - ct)
        tx = (W - s * W) / 2
        blank = PageObject.create_blank_page(width=W, height=H)
        blank.merge_transformed_page(page, Transformation().scale(s, s).translate(tx, ty))
        # cover is unnumbered so the report's own "shown on page N" references stay correct
        blank.merge_page(brand2._overlay(i - 1, total - 1, job["header_right"], job["foot"]))
        w.add_page(blank)
        log.append({"page": i, "old_header": head_cut is not None, "content_top": round(ct, 1),
                    "content_bottom": round(cb, 1), "scale": round(s, 4),
                    "new_top": round(new_top, 1), "new_bottom": round(new_top + s * (cb - ct), 1)})
    w.add_metadata({"/Title": job["title_meta"], "/Author": "Dimensure", "/Creator": "Dimensure",
                    "/Producer": "Dimensure"})
    with open(out, "wb") as f:
        w.write(f)
    plumb.close()
    os.remove(tmp_cover); os.remove(cleaned)
    return total, log


if __name__ == "__main__":
    src, out, jobf = sys.argv[1:4]
    total, log = rebrand(src, out, json.load(open(jobf)))
    print(json.dumps({"out": out, "pages": total, "log": log}))
