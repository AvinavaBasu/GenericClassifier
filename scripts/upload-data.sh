REMOTE_DIR=m.le@192.168.75.70:/home/m.le/generic-classifier
rsync -avh dicts/ $REMOTE_DIR/dicts/ --delete
rsync -avh ../datasets/ $REMOTE_DIR/datasets/ --delete
rsync -avh output/ $REMOTE_DIR/output/ --delete