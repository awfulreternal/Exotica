FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 EXOTICA_HOME=/data
WORKDIR /app
RUN groupadd --system exotica && useradd --system --gid exotica --home-dir /data exotica
COPY pyproject.toml README.md LICENSE ./
COPY exotica ./exotica
RUN pip install --no-cache-dir .
RUN mkdir -p /data && chown -R exotica:exotica /data
USER exotica
VOLUME ["/data"]
ENTRYPOINT ["exotica"]
CMD ["doctor"]
