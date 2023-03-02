FROM python:3.9.13

LABEL author="Rachel Duffin" \
    maintainer="rachel.duffin2@nhs.net"

RUN mkdir -p /duty_csv /outputs
ADD ./ /duty_csv
RUN pip3 install -r /duty_csv/requirements.txt
RUN ln /duty_csv/duty_csv.py /usr/local/bin/polyedge.py
WORKDIR /outputs
ENTRYPOINT [ "python3","/duty_csv/duty_csv.py" ]
