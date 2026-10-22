FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8080 DATABASE_PATH=/data/coldchain.sqlite
WORKDIR /app
COPY coldchain ./coldchain
COPY fixtures ./fixtures
RUN useradd --system --uid 10001 app && mkdir -p /data && chown app:app /data
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)" || exit 1
CMD ["python", "-m", "coldchain"]
