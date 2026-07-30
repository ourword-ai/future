#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bring EVERY finding up to the 2026-07-30 card standard (operator interview):
mined first-hand voices + does/why_use/gap/counter(risk)/differentiator(wedge)/value
(+zh copy) + verdict/workload via editor_pick — for all cards, not just score>=8.
Highest-visibility first, idempotent, throttled — re-runs daily until the whole
board is converted within the GitHub Models free quota."""
import os, sys, json, glob, time
sys.path.insert(0, "scouts")
import scout_lib as S

NEED_COPY = ("does", "gap", "counter", "differentiator")

items = []
for p in sorted(glob.glob("findings/*.json")):
    if os.path.basename(p) == "feed.json":
        continue
    try:
        items.append((p, json.load(open(p, encoding="utf-8"))))
    except Exception:
        pass

def prio(f):
    v = f.get("verdict") or ""
    tier = 0 if v == "build" else 1 if v == "watch" else 3 if v in ("archive", "drop") else 2
    return (tier, -(f.get("score") or 0))
items.sort(key=lambda x: prio(x[1]))

voices_done = copy_done = verdict_done = dropped = 0
for p, f in items:
    if f.get("verdict") == "drop":
        continue
    changed = False
    veto = S.integrity_veto(f)
    if veto:
        f["verdict"] = "drop"; f["drop_reason"] = veto; changed = True; dropped += 1
    else:
        if "voices" not in f:            # mine once; store [] so we don't re-mine daily
            try:
                f["voices"] = S.demand_voices(f)
            except Exception as e:
                print(f"  [voices skip] {e!r}", file=sys.stderr)
                f["voices"] = []
            changed = True; voices_done += 1; time.sleep(2)
        if any(not f.get(k) for k in NEED_COPY):
            c = S.llm_copy(f)
            if c is None:
                print("models limited/unavailable — stopping (re-run to continue)")
                if changed:
                    json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                break
            f.update(c); changed = True; copy_done += 1; time.sleep(3)
        if not f.get("verdict") or not f.get("workload"):
            pk, why, _sc, extra = S.editor_pick(f, f.get("voices"))
            if pk is None and not extra:
                print("models limited/unavailable — stopping (re-run to continue)")
                if changed:
                    json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                break
            if extra:
                f.update(extra)
            if "pick" not in f:
                f["pick"] = pk
                if why:
                    f["pick_reason"] = why
            changed = True; verdict_done += 1; time.sleep(3)
    if changed:
        json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(("✗" if f.get("verdict") == "drop" else "✓"),
              (f.get("title") or "")[:48],
              "| voices", len(f.get("voices") or []),
              "| verdict", f.get("verdict"), "| wl", f.get("workload"))
print(f"voices={voices_done} copied={copy_done} verdicts={verdict_done} dropped={dropped}")
S.refresh()
