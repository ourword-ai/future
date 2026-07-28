#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bilingual safety-net runner: translate any findings missing 中文. Run hourly by
.github/workflows/translate.yml (also workflow_dispatch). Capped + idempotent."""
import os, sys
sys.path.insert(0, "scouts")
import scout_lib as S
S.translate_missing(cap=int(os.environ.get("TRANSLATE_CAP", "8")))
