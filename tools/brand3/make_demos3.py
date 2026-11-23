"""Rebuild the five anonymised example reports (DEMO-01..05) in the RAMS look (kit3/brand3.py)."""
import json, sys
sys.path.insert(0, "kit3"); import brand3
J = {
 1: ("Road Surfacing Quality Check", "Housing development – Roads 1 and 2", "Binder course and kerbs as laid, before the surface course.", "November 2026"),
 2: ("Road Formation Quality Check", "Housing development – Roads 1 to 5", "Type 1 sub-base and kerbs as laid, against the drawings.", "November 2026"),
 3: ("Road Surfacing Quality Check", "Housing development – Roads 1 to 4", "Base and binder course as laid, with laid quantities.", "November 2026"),
 4: ("Substructure &amp; Internal Drainage", "Housing development – Plot 1", "Plot scan before the floor goes in: brickwork, levels and drainage.", "November 2026"),
 5: ("Plot / Oversite Quality Check", "Housing development – Plot 1", "Plot scan once the floor is down: brickwork, floor and drainage.", "November 2026"),
}
for n, (t, sub, desc, date) in J.items():
    ref = f"DEMO-0{n}"; plain = t.replace("&amp;", "&")
    cover = {"title": t, "subtitle": sub, "desc": desc,
             "meta": [("Reference", ref), ("Revision", "Rev 1"), ("Date", date),
                      ("Applies to", "Example report – client and<br>site details removed"), ("", None), ("Contact", "info@dimensure.co.uk")],
             "foot": (f"© 2026 Dimensure. Confidential. Ref {ref}, Rev 1.",
                      "Example report shown as a demonstration only – not to be copied, altered or relied on for design or construction."),
             "pdf_title": f"Dimensure — {plain} — example ({ref})"}
    r = brand3.restyle_existing(f"/home/claude/pack/files/{ref}.pdf", f"out3/{ref}.pdf", cover,
                                pill=f"{ref} · Rev 1",
                                foot_left=f"© 2026 Dimensure. Confidential. Example report – client and site details removed. Ref {ref}, Rev 1.")
    print(ref, json.dumps({k: v for k, v in r.items() if k != "log"}), [(l["page"], l["scale"]) for l in r["log"] if l["scale"] < 1])
