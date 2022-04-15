FROM python:3

WORKDIR /app

# RUN pip install --upgrade setuptools
RUN pip install poetry==1.1.12
# RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml /app/
RUN cd /app && poetry install --no-dev

ADD blockchain.py /app
EXPOSE 5000

CMD [ "python", "blockchain.py", "-p", "5000" ]