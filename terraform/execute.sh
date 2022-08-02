#!/bin/bash

CURRENT=$(cd $(dirname $0); pwd)
cd ${CURRENT}

proj=`gcloud projects list --format="value(project_id)" | fzf --header "[GCP Project]"`
gsutil cp -rp gs://${proj}-sa-master/terraform.json .

sed -i -e "s/PROJECT/${proj}/g" backend.tf

terraform init

if [ $? -ne 0 ]; then
    exit
fi

export TF_VAR_image_version=`cat ../version.txt`

terraform apply

sed -i -e "s/${proj}/PROJECT/g" backend.tf

rm -rf terraform.json

