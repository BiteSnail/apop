FROM python:3.11 

WORKDIR /djangoproject/
ADD . /djangoproject/

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN echo "yes" | python manage.py collectstatic 