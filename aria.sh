aria2c --enable-rpc=true --check-certificate=false --daemon=true \
   --max-connection-per-server=10 --rpc-max-request-size=1024M --quiet=true \
   --min-split-size=10M --split=10 --allow-overwrite=true \
   --max-overall-download-limit=0 --disk-cache=32M \
   --max-overall-upload-limit=1K --max-concurrent-downloads=15 --summary-interval=0 \
   --peer-id-prefix=-qB4420- --user-agent=Wget/1.12 \
   --bt-enable-lpd=true --max-file-not-found=0 --max-tries=20 --follow-torrent=mem \
   --auto-file-renaming=true --reuse-uri=true --http-accept-gzip=true --continue=true \
   --content-disposition-default-utf8=true 