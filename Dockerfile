FROM ubuntu:latest

RUN apt-get update && apt-get install -y python3.11 python3.11-distutils

RUN apt-get install -y python3.11 python3.11-distutils python3-pip

RUN apt-get install -y git

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY constants.py constants.py
COPY db_interactor.py db_interactor.py
COPY main.py main.py


CMD ["python3", "main.py"]
