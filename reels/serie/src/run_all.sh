#!/bin/bash
d=$1; cd /tmp/claude-0/-home-user-rac-privacy/60f45fd2-d7d3-53ee-935e-2e8fb9afed24/scratchpad/serie/$d || exit 1
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt REEL_HTML=reel.html
python3 -W ignore pipeline.py audio /home/user/rac-privacy/reels/serie/$d.mp4 > build.log 2>&1 && echo "LISTO $d" || echo "FALLO $d"
