FROM python:latest

# Install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /usr/bin/downloader-page

ENTRYPOINT ["python", "/usr/bin/downloader-page/app.py"]
