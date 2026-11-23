# -*- coding: utf-8 -*-
"""Dimensure document format, 2026 "RAMS look" (brand3) — matched to Dimensure RAMS – Site Survey
Services Rev 5.2 (21 Nov 2026), which Lewis confirmed on 23 Nov 2026 as the new look for every
Dimensure document. Supersedes brand2.py (navy header bar).

Cover : navy top block (#0D2530, 185 mm) with a 0.75 mm mint (#5EEAD4) line, white logo
        (logo_cover.png) top-left, title 34 pt white, subtitle 16 pt #C9D3DB, one-line description
        10 pt #8FA6B5; white band with detail columns (labels 7.5 pt green #16806A capitals,
        values 10 pt #0F1720), two copyright lines 6.6 pt #5B6773, photo strip (cover_strip.jpg).
Pages : WHITE header — navy-text vector logo (logo_header_dark.pdf) top-left, mint pill on the
        right (0.75 pt #2ED4A6 outline, 8 pt Inter SemiBold #0E8F6E, "REF · Rev n"), 1.4 pt navy
        (#071820) rule across the text width at 97 pt. Footer: one line 7 pt Inter #5B6770,
        "© 2026 Dimensure. Confidential. Ref …, Rev n." left, "Page x of y" right. No navy bar.
Body  : Inter; text #071820; H1 19 pt bold; H2 14 pt bold with a 2.2 pt mint (#2ED4A6) bar to
        the left; tables: header row #F1FAF6 with a mint underline, row rules #D9E2E6;
        labels green #0E8F6E. Text width 45.8–550.5 pt (16.2 mm sides).

Use render3() for new documents (HTML body) and restyle_existing() for finished PDFs that have
no HTML source. Never redraw the logo — use the files in this folder.
"""
import base64, os
import pymupdf

D = os.path.dirname(os.path.abspath(__file__))
NAVY = "#0D2530"; RULE = "#071820"; MINT = "#2ED4A6"; MINT_LINE = "#5EEAD4"
GREEN_TXT = "#0E8F6E"; GREEN_LBL = "#16806A"; INK = "#071820"; MUTED = "#5B6770"
LEFT, RIGHT = 45.8, 550.5            # text width, pt
BODY_TOP, BODY_BOTTOM = 112.0, 806.0  # usable body area on a page, pt from top
FONT = {"r": os.path.join(D, "fonts", "Inter-Regular.ttf"),
        "s": os.path.join(D, "fonts", "Inter-SemiBold.ttf"),
        "b": os.path.join(D, "fonts", "Inter-Bold.ttf")}


def _hex(c):
    c = c.lstrip("#"); return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _b64(p):
    return base64.b64encode(open(os.path.join(D, p), "rb").read()).decode()


# ───────────────────────── cover ─────────────────────────
def cover_html(c):
    """c: title, subtitle, desc, meta=[(label, value) …] (3 per row, value may hold <br>;
    a value of None leaves the cell empty), foot=(line1, line2)."""
    cells = "".join(
        f'<div class="m">' + (f'<div class="ml">{k}</div><div class="mv">{v}</div>' if v is not None else "") + "</div>"
        for k, v in c["meta"])
    fonts = "".join(
        f"@font-face{{font-family:Inter;font-weight:{w};src:url(data:font/ttf;base64,{_b64('fonts/' + f)})}}"
        for w, f in ((400, "Inter-Regular.ttf"), (600, "Inter-SemiBold.ttf"), (700, "Inter-Bold.ttf")))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fonts}
@page{{size:A4;margin:0}} html,body{{margin:0;padding:0}}
body{{font-family:Inter,"Liberation Sans",Arial,sans-serif;width:210mm;height:297mm;position:relative;overflow:hidden;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.top{{position:absolute;left:0;top:0;width:210mm;height:185mm;background:{NAVY}}}
.line{{position:absolute;left:0;top:185mm;width:210mm;height:.78mm;background:{MINT_LINE}}}
.logo{{position:absolute;left:20mm;top:18.66mm;width:52mm}}
.title{{position:absolute;left:20mm;top:86.5mm;width:170mm;color:#fff;font-size:34pt;font-weight:700;line-height:1.12}}
.sub{{position:absolute;left:20mm;top:{c.get('subtop', 128.2)}mm;width:170mm;color:#C9D3DB;font-size:16pt}}
.desc{{position:absolute;left:20mm;top:{c.get('subtop', 128.2) + 9.7}mm;width:170mm;color:#8FA6B5;font-size:10pt}}
.meta{{position:absolute;left:20mm;top:198.3mm;width:170mm;display:grid;grid-template-columns:56.7mm 56.7mm 56.7mm;row-gap:6.2mm}}
.ml{{font-size:7.5pt;font-weight:700;color:{GREEN_LBL};letter-spacing:.03em;text-transform:uppercase;margin-bottom:1.6mm}}
.mv{{font-size:10pt;color:#0F1720;line-height:1.3}}
.cr{{position:absolute;left:20mm;top:231.6mm;width:170mm;font-size:6.6pt;color:#5B6773;line-height:1.25}}
.strip{{position:absolute;left:0;bottom:0;width:210mm}}
</style></head><body>
<div class="top"></div><div class="line"></div>
<img class="logo" src="data:image/png;base64,{_b64('logo_cover.png')}">
<div class="title">{c['title']}</div><div class="sub">{c.get('subtitle', '')}</div><div class="desc">{c.get('desc', '')}</div>
<div class="meta">{cells}</div>
<div class="cr">{c['foot'][0]}<br>{c['foot'][1]}</div>
<img class="strip" src="data:image/jpeg;base64,{_b64('cover_strip.jpg')}">
</body></html>"""


def _chrome_pdf(html, path, margins):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome"); pg = b.new_page()
        pg.set_content(html, wait_until="load")
        pg.pdf(path=path, format="A4", print_background=True, margin=margins)
        b.close()


# ───────────────────────── header / footer ─────────────────────────
def dress_page(page, pill, foot_left, n, total):
    """Draw the RAMS-style header and footer on a pymupdf page (A4)."""
    logo = pymupdf.open(os.path.join(D, "logo_header_dark.pdf"))
    page.show_pdf_page(pymupdf.Rect(46.5, 51.5, 165.5, 85.5), logo, 0)
    # pill: text right-aligned, 6.4 pt padding, 15 pt tall, right edge 550.1
    fs = pymupdf.Font(fontfile=FONT["s"]); tw = fs.text_length(pill, 7.99)
    x1 = 550.1; x0 = x1 - tw - 12.8
    page.draw_rect(pymupdf.Rect(x0, 61.1, x1, 76.1), color=_hex(MINT), width=0.75, radius=0.5)
    page.insert_text((x0 + 6.4, 71.3), pill, fontsize=7.99, fontname="InterSB", fontfile=FONT["s"], color=_hex(GREEN_TXT))
    page.draw_rect(pymupdf.Rect(LEFT, 96.8, RIGHT, 98.2), color=None, fill=_hex(RULE), width=0)
    # footer
    page.insert_text((45.4, 826.0), foot_left, fontsize=7.0, fontname="InterR", fontfile=FONT["r"], color=_hex(MUTED))
    pn = f"Page {n} of {total}"; fr = pymupdf.Font(fontfile=FONT["r"])
    page.insert_text((550.6 - fr.text_length(pn, 7.0), 826.0), pn, fontsize=7.0, fontname="InterR", fontfile=FONT["r"], color=_hex(MUTED))


# ───────────────────────── new documents (HTML body) ─────────────────────────
BODY_CSS = f"""
body{{font-family:Inter,"Liberation Sans",Arial,sans-serif;color:{INK};font-size:9.5pt;line-height:1.5}}
h1{{font-size:19pt;font-weight:700;color:{INK};margin:0 0 4mm}}
h2{{font-size:14pt;font-weight:700;color:{INK};border-left:2.2pt solid {MINT};padding-left:8.5pt;margin:7mm 0 3mm;line-height:1.45}}
h3{{font-size:10.5pt;font-weight:700;color:{INK}}}
.label{{font-size:7.5pt;font-weight:700;color:{GREEN_TXT};letter-spacing:.03em;text-transform:uppercase}}
table{{border-collapse:collapse;width:100%}}
th{{background:#F1FAF6;color:{INK};font-weight:600;text-align:left;border-bottom:1.1pt solid {MINT};padding:2.2mm 2mm}}
td{{border-bottom:.7pt solid #D9E2E6;padding:1.9mm 2mm;vertical-align:top}}
.note{{border-left:2.2pt solid {MINT};background:#F1FAF6;padding:3mm 4mm}}
"""


def render3(body_html, out, cover, pill, foot_left, extra_css=""):
    """body_html: a full HTML document with its own <style>. cover: see cover_html (foot = 2 lines).
    The cover is page 1 and is counted, as in the RAMS."""
    fonts = cover_html(dict(cover)).split("<style>")[1].split("@page")[0]
    body_html = body_html.replace("</style>", fonts + BODY_CSS + extra_css + "</style>", 1)
    tc, tb = out + ".c.tmp.pdf", out + ".b.tmp.pdf"
    _chrome_pdf(cover_html(cover), tc, {"top": "0", "bottom": "0", "left": "0", "right": "0"})
    _chrome_pdf(body_html, tb, {"top": f"{BODY_TOP}pt", "bottom": f"{842 - BODY_BOTTOM}pt", "left": "16.2mm", "right": "16.2mm"})
    doc = pymupdf.open(tc); doc.insert_pdf(pymupdf.open(tb))
    for i, p in enumerate(doc):
        if i: dress_page(p, pill, foot_left, i + 1, len(doc))
    doc.save(out, garbage=3, deflate=True); os.remove(tc); os.remove(tb)
    return len(doc)


# ───────────────────────── finished PDFs (no HTML source) ─────────────────────────
# old toolkit palette → RAMS palette (colour only; chips/figure colours untouched)
PALETTE = {"#3e5560": INK, "#0b222c": INK, "#d5e0dc": "#D9E2E6", "#e1e9e6": "#D9E2E6",
           "#eef3f1": "#F1FAF6"}
ACCENT_OLD = "#2f8f78"   # → mint bar (#2ED4A6) when used as a fill, green #0E8F6E when used for text


def remap_palette(path_in, path_out):
    import pikepdf
    pdf = pikepdf.open(path_in)
    targets = {tuple(round(v * 255) for v in _hex(k)): v for k, v in PALETTE.items()}
    acc = tuple(round(v * 255) for v in _hex(ACCENT_OLD))
    changed = [0]

    def fix(stream_owner):
        ops = pikepdf.parse_content_stream(stream_owner)
        out, in_text = [], False
        for operands, op in ops:
            o = str(op)
            if o == "BT": in_text = True
            elif o == "ET": in_text = False
            if o in ("rg", "RG", "sc", "scn", "SC", "SCN") and len(operands) == 3:
                try:
                    v = tuple(round(float(x) * 255) for x in operands)
                except Exception:
                    v = None
                new = None
                if v is not None:
                    for t, n in targets.items():
                        if max(abs(a - b) for a, b in zip(v, t)) <= 1: new = n
                    if max(abs(a - b) for a, b in zip(v, acc)) <= 1:
                        new = GREEN_TXT if in_text else MINT
                if new:
                    operands = [pikepdf.objects.Object.parse(f"{x:.4f}".encode()) for x in _hex(new)]
                    changed[0] += 1
            out.append((operands, op))
        stream_owner.write(pikepdf.unparse_content_stream(out)) if isinstance(stream_owner, pikepdf.Stream) else None
        return out

    def walk(obj, seen):
        if obj.objgen in seen: return
        seen.add(obj.objgen)
        res = obj.get("/Resources")
        if res is not None and "/XObject" in res:
            for _, x in res.XObject.items():
                if x.get("/Subtype") == "/Form":
                    fix(x); walk(x, seen)

    for page in pdf.pages:
        new = fix(page.obj)
        page.obj.Contents = pdf.make_stream(pikepdf.unparse_content_stream(new))
        walk(page.obj, set())
    pdf.save(path_out)
    return changed[0]


def _old_header_cut(pg):
    """pdfplumber page → y just below an old-toolkit header (DIMENSURE wordmark + rule) or None."""
    words = pg.extract_words()
    if not any(w["text"] == "DIMENSURE" and w["top"] < 60 for w in words): return None
    rules = [r for r in (pg.lines + pg.rects) if r["top"] < 95 and r["width"] > 300 and r["height"] < 3]
    return (max(r["bottom"] for r in rules) if rules else 80.0) + 1.5


def restyle_existing(src, out, cover, pill, foot_left, number_cover=False):
    """Re-dress a finished old-toolkit PDF: redact its old header/footer, remap the palette, move
    (and only if needed uniformly scale) content into the body area, add the RAMS cover, header and
    footer. number_cover=False keeps the report's own page numbers (and its "page N" references)."""
    import pdfplumber
    tmp1, tmp2, tc = out + ".1.tmp.pdf", out + ".2.tmp.pdf", out + ".c.tmp.pdf"
    with pdfplumber.open(src) as p:
        cuts = [_old_header_cut(pg) for pg in p.pages]
    d = pymupdf.open(src)
    for page, cut in zip(d, cuts):
        r = page.rect
        if cut is not None: page.add_redact_annot(pymupdf.Rect(0, 0, r.width, cut), fill=False)
        page.add_redact_annot(pymupdf.Rect(0, r.height - 30, r.width, r.height), fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    d.save(tmp1, garbage=3, deflate=True)
    nmap = remap_palette(tmp1, tmp2)
    # content boxes after cleaning
    boxes = []
    with pdfplumber.open(tmp2) as p:
        for pg, cut in zip(p.pages, cuts):
            H = pg.height; tops, bots = [], []
            for o in pg.chars + pg.lines + pg.rects + pg.curves + pg.images:
                if o.get("width", 0) > pg.width - 10 and o.get("height", 0) > H - 10: continue
                if cut is not None and o["bottom"] <= cut + 0.5: continue
                if o["top"] >= H - 30: continue
                tops.append(o["top"]); bots.append(o["bottom"])
            boxes.append((min(tops), max(bots)))
    _chrome_pdf(cover_html(cover), tc, {"top": "0", "bottom": "0", "left": "0", "right": "0"})
    srcdoc = pymupdf.open(tmp2)
    outdoc = pymupdf.open(tc)
    nbody = len(srcdoc); total = nbody + (1 if number_cover else 0)
    log = []
    for i, (ct, cb) in enumerate(boxes):
        W, H = srcdoc[i].rect.width, srcdoc[i].rect.height
        avail = BODY_BOTTOM - BODY_TOP
        top = max(ct, BODY_TOP)                       # never move content up; move down only if needed
        s = min(1.0, (BODY_BOTTOM - top) / (cb - ct)) if cb - ct > 0 else 1.0
        if s < 1.0:                                   # does not fit below: use the whole body area
            top = BODY_TOP; s = min(1.0, avail / (cb - ct))
        dy = top - s * ct; dx = (W - s * W) / 2
        page = outdoc.new_page(width=W, height=H)
        page.show_pdf_page(pymupdf.Rect(dx, dy, dx + s * W, dy + s * H), srcdoc, i)
        n = i + (2 if number_cover else 1)
        dress_page(page, pill, foot_left, n, total)
        log.append({"page": n, "scale": round(s, 4), "top": round(top, 1), "bottom": round(top + s * (cb - ct), 1)})
    outdoc.set_metadata({"title": cover.get("pdf_title", ""), "author": "Dimensure", "creator": "Dimensure", "producer": "Dimensure"})
    outdoc.save(out, garbage=3, deflate=True)
    for t in (tmp1, tmp2, tc): os.remove(t)
    return {"pages": len(outdoc), "palette_changes": nmap, "log": log}
