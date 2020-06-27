FROM python:3 AS builder

ADD pyproject.toml /
ADD xtract /xtract/

RUN ls -la xtract
RUN pip install poetry

RUN poetry build

#COPY dist/service_1-0.1.0.tar.gz .

FROM python:3 AS run

RUN ls -la
COPY --from=builder /dist/xtract-*.tar.gz .
RUN python -m pip install xtract-*.tar.gz


CMD [ "gunicorn", "xtract:prod_app", "--bind", "0.0.0.0:9000"]
EXPOSE 9000/tcp