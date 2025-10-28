import os
from pathlib import Path
import polib

BASE_DIR = Path(__file__).resolve().parents[1]
po_path = BASE_DIR / 'locale' / 'bn' / 'LC_MESSAGES' / 'django.po'
mo_path = BASE_DIR / 'locale' / 'bn' / 'LC_MESSAGES' / 'django.mo'

if not po_path.exists():
    raise SystemExit(f".po file not found: {po_path}")

po = polib.pofile(str(po_path))
# Optionally validate entries
po.save_as_mofile(str(mo_path))
print(f"Compiled {po_path} -> {mo_path} ({len(po)} entries)")
