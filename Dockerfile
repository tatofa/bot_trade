FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Fail build fast if unresolved Git conflict markers were committed.
RUN python - <<'PY'
from pathlib import Path
markers = ("<" * 7, "=" * 7, ">" * 7)
for path in Path('/app').glob('*.py'):
    text = path.read_text(encoding='utf-8')
    if any(m in text for m in markers):
        raise SystemExit(f"Unresolved merge markers in {path}")
print('merge-marker check passed')
PY

RUN python -m py_compile *.py

CMD ["python", "run_bot.py"]
