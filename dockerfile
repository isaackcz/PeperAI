FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 5000

CMD ["python", "backend/app.py"]