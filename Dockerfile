FROM python:3.6-alpine
COPY requirements.txt /usr/src/cost_reporter/requirements.txt
RUN pip install -r /usr/src/cost_reporter/requirements.txt
COPY cost_reporter.py /usr/src/cost_reporter/cost_reporter.py
ENTRYPOINT ["python","/usr/src/cost_reporter/cost_reporter.py"]
