# P0-IF positive control image, version 1.2 (HANFIS A-01/A-11, amendment A-15).
#
# Derived DIRECTLY from the P0 baseline image, pinned by digest, so that P0-IF carries
# exactly P0's package set and CVE surface (Alpine 3.21.3; 109 CVEs at DB 2026-09-14,
# 25 of them in libexpat). The base already contains ngx_http_image_filter_module.so,
# libgd.so.3, libexpat.so.1 and scanelf (pax-utils), which is everything the
# reachability-evidence protocol needs.
#
# NO `apk add` here: apk would fetch the *current* Alpine 3.21 package versions and
# silently patch the CVEs the control depends on (this is how image 1.1 ended up with
# 0 CVEs). Fence P13: base pinned by digest, tag never rewritten.
#
# OFF and ON variants use THIS image; only the mounted nginx.conf differs (p0if.yaml).
FROM nginxinc/nginx-unprivileged@sha256:65e3e85dbaed8ba248841d9d58a899b6197106c23cb0ff1a132b7bfe0547e4c0

USER root
# A tiny JPEG so the image_filter location (/resize/sample.jpg) has something to process.
COPY sample.jpg /usr/share/nginx/html/sample.jpg
# Exact package versions inside the image: part of the identity evidence bundle.
RUN apk list --installed | sort > /usr/share/nginx/html/apk-installed.txt \
 && chown 101:101 /usr/share/nginx/html/sample.jpg /usr/share/nginx/html/apk-installed.txt
USER 101
EXPOSE 8080
# ENTRYPOINT/CMD inherited from the base (docker-entrypoint.sh + nginx -g "daemon off;").
