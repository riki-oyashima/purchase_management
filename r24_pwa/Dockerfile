FROM python:3.7.4-slim-stretch

ENV PYTHONPATH=/purchase_management/
ENV GOOGLE_APPLICATION_CREDENTIALS=/purchase_management/r24_pwa/service.json

COPY . ${PYTHONPATH}r24_pwa/

RUN apt-get update \
    && apt-get install -y apt-utils g++ default-libmysqlclient-dev libeccodes-dev \
    && apt-get install -y tzdata \
    && cp -f /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ${PYTHONPATH}r24_pwa/requirements.txt \
    && apt-get clean \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /var/log/nrgp

WORKDIR ${PYTHONPATH}
RUN ${PYTHONPATH}r24_pwa/manage.py collectstatic --no-input

CMD ["uwsgi","--ini","r24_pwa/api/uwsgi.ini","--static-map","/static=collected_static"]
