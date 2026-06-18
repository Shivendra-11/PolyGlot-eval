FROM python:3.12-slim
WORKDIR /app
COPY app/ app/
COPY tests/ tests/
EXPOSE 8080
CMD ["python", "-c", "print('fixture-repo ok')"]
