# Copyright 2015 - Alidron's authors
#
# This file is part of Alidron.
#
# Alidron is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alidron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Alidron.  If not, see <http://www.gnu.org/licenses/>.

image_name = alidron/alidron-isac
rpi_image_name = alidron/rpi-alidron-isac
registry = registry.tinigrifi.org:5000
rpi_registry = neuron.local:6667

network_name = alidron

.PHONY: clean clean-dangling build build-rpi push push-rpi pull pull-rpi run-bash run run1 run1-rpi run2 run2-rpi run3 test1 test2 unittest unittest-rpi unittest-live

clean:
	docker rmi $(image_name) || true

clean-dangling:
	docker rmi `docker images -q -f dangling=true` || true

build: clean-dangling
	docker build --force-rm=true -t $(image_name) .

build-rpi: clean-dangling
	docker build --force-rm=true -t $(rpi_image_name) -f Dockerfile-rpi .

push:
	docker tag -f $(image_name) $(registry)/$(image_name)
	docker push $(registry)/$(image_name)

push-rpi:
	docker tag -f $(rpi_image_name) $(rpi_registry)/$(rpi_image_name)
	docker push $(rpi_registry)/$(rpi_image_name)

pull:
	docker pull $(registry)/$(image_name)
	docker tag $(registry)/$(image_name) $(image_name)

pull-rpi:
	docker pull $(rpi_registry)/$(rpi_image_name)
	docker tag $(rpi_registry)/$(rpi_image_name) $(rpi_image_name)

run-bash:
	docker run -it --net=$(network_name) --rm -v /media/data/Informatique/Python/Netcall/netcall:/usr/src/netcall -v `pwd`:/usr/src/alidron-isac/isac $(image_name) bash

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
	docker run --rm --name alidron-isac-unittest $(image_name) py.test -s --cov-report term-missing --cov-config /usr/src/alidron-isac/isac/.coveragerc --cov=isac /usr/src/alidron-isac

unittest-rpi:
	docker run --rm --name alidron-isac-unittest $(rpi_image_name) py.test -s --cov-report term-missing --cov-config /usr/src/alidron-isac/isac/.coveragerc --cov=isac /usr/src/alidron-isac

unittest-live:
	docker run --rm --name alidron-isac-unittest -v `pwd`:/usr/src/alidron-isac/isac $(image_name) py.test -s --cov-report term-missing --cov-config /usr/src/alidron-isac/isac/.coveragerc --cov=isac /usr/src/alidron-isac # -k test_create_many
