FROM python:3.10-slim

RUN mkdir /app
COPY litellm-updater.py /app
WORKDIR /app

RUN pip install requests

CMD ["python", "litellm-updater.py"]