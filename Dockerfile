FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends libgomp1 \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY Aiml ./Aiml
COPY app.py ./app.py

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
