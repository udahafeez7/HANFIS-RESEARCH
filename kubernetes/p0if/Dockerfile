# P0-IF positive control image (HANFIS amendment A-01, patch 0014).
#
# Purpose: create a workload in which the libexpat code path is genuinely reachable,
# so that the applicability dataset contains APPLICABLE_OBSERVED rows and not only
# NA_OBSERVED_DEPLOYMENT. nginx's image_filter module links against libgd, which in
# turn links against libexpat; loading the module and configuring an image_filter
# location makes both libraries appear in the process memory map.
#
# Both the OFF and the ON variant are built from THIS image, so the only difference
# between the two conditions is the nginx configuration (module loaded or not).
# The original p0-baseline deployment (nginxinc/nginx-unprivileged:1.27-alpine) is
# never modified; telemetry continuity with Runs 7-17 is preserved.

FROM alpine:3.21

RUN apk add --no-cache \
      nginx \
      nginx-mod-http-image-filter \
      gd \
      expat \
      curl \
 && mkdir -p /var/lib/nginx/tmp /var/log/nginx /usr/share/nginx/html \
 && chown -R 101:101 /var/lib/nginx /var/log/nginx /usr/share/nginx/html

# A tiny JPEG so the image_filter location has something to process.
COPY sample.jpg /usr/share/nginx/html/sample.jpg

# Record the exact package versions inside the image: this file is part of the
# identity evidence and is hashed together with the rest of the bundle.
RUN apk list --installed | sort > /usr/share/nginx/html/apk-installed.txt \
 && chown 101:101 /usr/share/nginx/html/apk-installed.txt

USER 101
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
