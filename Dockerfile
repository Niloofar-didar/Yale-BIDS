FROM python:3.9-slim

WORKDIR /app

EXPOSE 5000
ENV FLASK_APP=app.py

COPY . /app
RUN pip install --no-cache-dir Flask Flask-RestX flask-restful requests beautifulsoup4


ENTRYPOINT [ "flask"]
CMD [ "run", "--host", "0.0.0.0" ]
