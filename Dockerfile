# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

FROM alidron/alidron-base-python:3-slim
MAINTAINER Axel Voitier <axel.voitier@gmail.com>

COPY dist/ /app/dist/
WORKDIR /app
RUN pip install --no-cache-dir dist/* && rm -R dist

CMD ["python3", "-m", "isac_cmd"]
