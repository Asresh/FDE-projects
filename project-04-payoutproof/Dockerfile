FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8090 DATABASE_PATH=/data/payoutproof.sqlite
WORKDIR /app
COPY payoutproof ./payoutproof
COPY fixtures ./fixtures
RUN useradd --system --uid 10001 app && mkdir -p /data && chown app:app /data
USER app
EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=2)" || exit 1
CMD ["python", "-m", "payoutproof"]
