DATE=$(date +"%m-%d-%Y")"|"$(date +"%T")
set -xe
git add .
git commit -m "$DATE"
git push