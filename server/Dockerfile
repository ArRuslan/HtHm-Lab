FROM python:3.9-alpine

RUN apk add libmagic
RUN python -m pip install --upgrade pip wheel setuptools

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["uvicorn", "src.main:app", "--forwarded-allow-ips='*'", "--host", "0.0.0.0", "--port", "8080"]