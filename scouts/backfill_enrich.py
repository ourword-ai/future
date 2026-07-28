#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-enrich existing findings with the NEW sharp bilingual copy (and editor picks).
Highest-score first, idempotent (skips items already bilingual/tagged), throttled — so it
can be re-run across days to finish within the GitHub Models free quota."""
import os, sys, json, glob, time
sys.path.insert(0, "scouts")
import scout_lib as S

items = []
for p in sorted(glob.glob("findings/*.json")):
    if os.path.basename(p) == "feed.json":
        continue
    try:
        items.append((p, json.load(open(p, encoding="utf-8"))))
    except Exception:
        pass
items.sort(key=lambda x: -(x[1].get("score") or 0))   # best first — most visible

copy_done = pick_done = 0
for p, f in items:
    changed = False
    if "i18n" not in f:                      # regenerate sharp, bilingual copy
        c = S.llm_copy(f)
        if c is None:
            print("models limited/unavailable — stopping (re-run to continue)")
            break
        f.update(c); changed = True; copy_done += 1
        time.sleep(3)
    if (f.get("score") or 0) >= 8 and "pick" not in f:
        pk, why = S.editor_pick(f)
        if pk is not None:
            f["pick"] = pk
            if why:
                f["pick_reason"] = why
            changed = True; pick_done += 1
            time.sleep(3)
    if changed:
        json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(("★" if f.get("pick") else " "), ("双" if "i18n" in f else " "), (f.get("title") or "")[:46])
print(f"re-copied={copy_done} picked={pick_done}")
S.refresh()
