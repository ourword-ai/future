#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resolver — the verification step. Finds due predictions and grades them by
checking the real public metric (auto ✅/❌). This is the cheapest real verification:
no reproduction, no staking — just wait for the deadline and check one number."""
import os, sys, json, glob, datetime, subprocess as sp
sys.path.insert(0, "scouts")
sys.path.insert(0, os.getcwd())
import scout_lib as S  # noqa: E402

def gh_comment(number, body):
    try:
        sp.run(["gh", "issue", "comment", str(number), "--body", body], capture_output=True, text=True)
    except Exception:
        pass

def main():
    today = datetime.date.today().isoformat()
    changed = 0
    for p in sorted(glob.glob("findings/*.json")):
        if os.path.basename(p) == "feed.json":
            continue
        try:
            f = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        pred = f.get("prediction") or {}
        if f.get("status") != "pending" or not pred:
            continue
        if (pred.get("resolve_on") or "9999-99-99") > today:
            continue  # not due yet
        try:
            obs = S.metric_value(pred)
        except Exception as e:
            print(f"  metric fetch failed for {f.get('id')}, will retry next run: {e!r}")
            continue
        if obs is None:
            continue
        op = pred.get("op", ">=")
        hit = (obs >= pred["target"]) if op == ">=" else (obs <= pred["target"])
        f["status"] = "hit" if hit else "miss"
        f["observed"] = obs
        f["resolved_at"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        changed += 1
        num = (f.get("id") or "").split("-")[0]
        if num.isdigit():
            verdict = "✅ HIT" if hit else "❌ MISS"
            gh_comment(num, f"{verdict} — observed **{obs:,}** (predicted {op} {pred.get('target'):,} "
                            f"by {pred.get('resolve_on')}). Verified by re-checking the public metric.")
        print(f"  resolved {f.get('id')}: {'HIT' if hit else 'MISS'} (obs={obs}, target={pred['target']})")
    if changed:
        S.refresh()
    print(json.dumps({"resolved": changed}))

if __name__ == "__main__":
    main()
