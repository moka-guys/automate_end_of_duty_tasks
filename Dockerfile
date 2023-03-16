FROM python:3.10.6

LABEL author="Rachel Duffin" \
    maintainer="rachel.duffin2@nhs.net"

RUN mkdir -p /duty_csv /outputs
ADD ./requirements.txt /duty_csv/
RUN pip3 install -r /duty_csv/requirements.txt
ADD ./*.py /duty_csv/
ADD ./templates/ /duty_csv/templates/
WORKDIR /outputs
ENTRYPOINT [ "python3","/duty_csv/duty_csv.py" ]
