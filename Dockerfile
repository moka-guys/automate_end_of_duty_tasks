FROM python:3.9.13-slim-bullseye
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python", "duty_csv.py"]
