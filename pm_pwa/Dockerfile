FROM python:3.7.4-slim-stretch

ENV PYTHONPATH=/purchase_management/
ENV GOOGLE_APPLICATION_CREDENTIALS=/purchase_management/pm_pwa/service.json

COPY . ${PYTHONPATH}pm_pwa/

RUN apt-get update \
    && apt-get install -y apt-utils g++ default-libmysqlclient-dev libeccodes-dev \
    && apt-get install -y tzdata \
    && cp -f /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ${PYTHONPATH}pm_pwa/requirements.txt \
    && apt-get clean \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /var/log/nrgp

WORKDIR ${PYTHONPATH}
RUN ${PYTHONPATH}pm_pwa/manage.py collectstatic --no-input

CMD ["uwsgi","--ini","pm_pwa/api/uwsgi.ini","--static-map","/static=collected_static"]
