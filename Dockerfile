FROM python:3.12-slim

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get purge -y imagemagick imagemagick-6-common \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        nodejs \
        npm \
        curl \
        git \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN python3 -m pip install --upgrade \
    setuptools==78.1.1 \
    gitpython==3.1.41

COPY ./scripts/install-subversion.sh /tmp/install-subversion.sh
RUN chmod +x /tmp/install-subversion.sh \
  && /tmp/install-subversion.sh \
  && rm -f /tmp/install-subversion.sh

RUN curl -sSL https://sdk.cloud.google.com | bash /dev/stdin --disable-prompts --install-dir=/usr/local


ENV PATH="$PATH:/usr/local/google-cloud-sdk/bin"
ENV CLOUDSDK_PYTHON=python3

COPY . /app/