FROM python:3.10.6

LABEL author="Rachel Duffin" \
    maintainer="rachel.duffin2@nhs.net"

RUN git clone https://github.com/moka-guys/duty_csv && cd duty_csv && git checkout v2.4.0
RUN mkdir -p /outputs
RUN pip3 install -r /duty_csv/requirements.txt
WORKDIR /outputs
ENTRYPOINT [ "python3","/duty_csv/duty_csv.py" ]
