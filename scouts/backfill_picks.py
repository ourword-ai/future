#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time (re-runnable) editor-pick backfill: tag existing high-score findings.
Idempotent (skips ones already tagged) and throttled, so it can be re-run if the
GitHub Models quota is hit mid-way."""
import os, sys, json, glob, time
sys.path.insert(0, "scouts")
import scout_lib as S

done = tagged = 0
for p in sorted(glob.glob("findings/*.json")):
    if os.path.basename(p) == "feed.json":
        continue
    try:
        f = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if (f.get("score") or 0) < 8 or "pick" in f:
        continue
    pk, why, _sc, _extra = S.editor_pick(f, S.demand_voices(f))
    if pk is None:
        print("model unavailable/limited — stopping (re-run later to continue)")
        break
    if _extra:
        f.update(_extra)
    f["pick"] = pk
    if why:
        f["pick_reason"] = why
    json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    done += 1; tagged += 1 if pk else 0
    print(("★" if pk else "·"), (f.get("title") or "")[:52])
    time.sleep(3)
print(f"processed={done} picked={tagged}")
S.refresh()
