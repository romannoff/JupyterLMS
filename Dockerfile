FROM python:3.9-slim

WORKDIR /app

COPY lms/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY lms/ /app/

RUN chmod +x /app/entrypoint.sh

EXPOSE 8008

ENTRYPOINT ["/app/entrypoint.sh"]