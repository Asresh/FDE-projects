FROM python:3.12-slim
WORKDIR /app
COPY signaldesk ./signaldesk
COPY data ./data
COPY web ./web
EXPOSE 8000
USER 10001
CMD ["python", "-m", "signaldesk"]
