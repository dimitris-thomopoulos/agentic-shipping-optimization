# We pin to version 1.76.0 which IS Alpine-based.
# This guarantees 'apk' will be available.

# dont change the n8n version! we stick to this
FROM n8nio/n8n:1.76.0

USER root

# Install Python 3 using apk
RUN apk add --update --no-cache python3 py3-pip

USER node