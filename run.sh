#!/bin/sh

set -x

python3 ytdlp.py $@

if [[ "${2}" == "DRM" ]] || [[ "${2}" == "drm" ]]; then
    # do something later
    echo "DRM content require decryption"
fi