# stage 1: base build stage
FROM python:3.14-slim AS builder

# create the app directory
RUN mkdir /app

# set the working directory to /app
WORKDIR /app

# set environment variables
# prevent python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# upgrade pip
RUN pip install --upgrade pip

# copy the django project and install dependencies
COPY requirements.txt /app/

# run this command to install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# stage 2: production stage
FROM python:3.14-slim

RUN useradd -m -r -u 10001 appuser && \
    mkdir /app && \
    chown -R appuser /app

# copy the python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# set the working directory to /app
WORKDIR /app

# copy the application code
COPY --chown=appuser:appuser . .

# collect static files
RUN python manage.py collectstatic --noinput

# set the environment variables to optimize python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/appuser

# set the user to appuser
USER appuser

# expose port 8000 for the django app
EXPOSE 8000

# start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "metadata.wsgi:application"]

