FROM python:3.12-slim
COPY src/ /app/src
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
ENV PYTHONPATH="${PYTHONPATH}:/app"
ENTRYPOINT ["python", "src/entrypoint.py"]
