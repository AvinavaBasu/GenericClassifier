REMOTE_DIR=m.le@192.168.75.43:/home/m.le/generic-classifier
rsync --exclude /output --exclude /target -avh . $REMOTE_DIR
rsync -avh dicts $REMOTE_DIR/../ --delete
rsync -avh ../datasets $REMOTE_DIR/../ --delete
