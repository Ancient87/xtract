FROM python:3 AS builder

ADD pyproject.toml /
ADD app/* /app/

RUN pip install poetry

RUN poetry build
RUN ls -la dist
#COPY dist/service_1-0.1.0.tar.gz .

FROM python:3 AS run

RUN ls -la
COPY --from=builder /dist/xtract-0.1.0.tar.gz .
RUN python -m pip install xtract-0.1.0.tar.gz

CMD [ "gunicorn", "xtract:app", "--bind", "0.0.0.0:9000"]
EXPOSE 9000/tcp