# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

image_name = alidron/alidron-isac
rpi_image_name = alidron/rpi-alidron-isac
private_rpi_registry = neuron.local:6667

network_name = alidron

.PHONY: clean clean-dangling build-wheel build build-rpi push push-rpi push-rpi-priv pull pull-rpi pull-rpi-priv run-bash run run1 run1-rpi run2 run2-rpi run3 test1 test2 unittest unittest-rpi unittest-live

clean:
	docker rmi $(image_name) || true

clean-dangling:
	docker rmi `docker images -q -f dangling=true` || true

build-wheel:
	rm -rf alidron_isac.egg-info build dist
	python3 setup.py bdist_wheel

build: clean-dangling build-wheel
	docker build --force-rm=true -t $(image_name) .

build-rpi: clean-dangling
	docker build --force-rm=true -t $(rpi_image_name) -f Dockerfile-rpi .

push:
	docker push $(image_name)

push-rpi:
	docker push $(rpi_image_name)

push-rpi-priv:
	docker tag -f $(rpi_image_name) $(private_rpi_registry)/$(rpi_image_name)
	docker push $(private_rpi_registry)/$(rpi_image_name)

pull:
	docker pull $(image_name)

pull-rpi:
	docker pull $(rpi_image_name)

pull-rpi-priv:
	docker pull $(private_rpi_registry)/$(rpi_image_name)
	docker tag $(private_rpi_registry)/$(rpi_image_name) $(rpi_image_name)

run-bash:
	docker run -it --net=$(network_name) --rm $(image_name) bash

run:
	docker run -it --net=$(network_name) --rm -v `pwd`/_logs:/logs $(image_name) python -m isac_cmd hello

run-alidron-test:
	docker run -it --net=$(network_name)-test --rm -v `pwd`/_logs:/logs $(image_name) python -m isac_cmd hello

run-rpi:
	docker run -it --net=$(network_name) --rm $(rpi_image_name) python -m isac_cmd hello

run1:
	docker run -it --net=$(network_name) --rm $(image_name) python isac_cmd.py gdsjkl01 # test01 gdsjkl01

run1-rpi:
	docker run -it --net=$(network_name) --rm $(rpi_image_name) python -m isac_cmd gdsjkl01 # test01 gdsjkl01

run2:
	docker run -it --net=$(network_name) --rm $(image_name) python isac_cmd.py fdsfds02 # test02 fdsfds02

run2-rpi:
	docker run -it --net=$(network_name) --rm $(rpi_image_name) python -m isac_cmd fdsfds02 # test02 fdsfds02

run3:
	docker run -it --net=$(network_name) --rm $(image_name) python -i isac.py test03

test1:
	docker run -it --net=$(network_name) --rm $(image_name) python test.py test01

test2:
	docker run -it --net=$(network_name) --rm $(image_name) python test.py test02

unittest:
	docker run --rm --name alidron-isac-unittest -v `pwd`/tests:/app/tests $(image_name) py.test -s --cov-report term-missing --cov-config /app/tests/.coveragerc --cov=isac /app/tests

unittest-rpi:
	docker run --rm --name alidron-isac-unittest -v `pwd`/tests:/app/tests $(rpi_image_name) py.test -s --cov-report term-missing --cov-config /app/tests/.coveragerc --cov=isac /app/tests

unittest-live:
	docker run --rm --name alidron-isac-unittest -v `pwd`/tests:/app/tests -v `pwd`/isac:/app/isac -e PYTHONPATH=/app $(image_name) py.test -s --cov-report term-missing --cov-config /app/tests/.coveragerc --cov=isac /app/tests -x # -k test_create_many
