FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# requirements.txt might be explicitly encoded in UTF-16, let's fix that during copy if pip fails
RUN pip install --no-cache-dir -r requirements.txt || \
    (iconv -f UTF-16 -t UTF-8 requirements.txt > req.txt && pip install --no-cache-dir -r req.txt)

COPY . .

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
