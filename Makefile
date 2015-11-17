image_name = alidron/alidron-isac
rpi_image_name = alidron/rpi-alidron-isac
#registry = neuron.local:6667
registry = registry.tinigrifi.org:5000

network_name = alidron

.PHONY: clean clean-dangling build build-rpi push push-rpi pull pull-rpi run-bash run run1 run1-rpi run2 run2-rpi run3 test1 test2

clean:
	docker rmi $(image_name) || true

clean-dangling:
	docker rmi $(docker images -q -f dangling=true) || true

build: clean-dangling
	docker build --force-rm=true -t $(image_name) .

build-rpi: clean-dangling
	docker build --force-rm=true -t $(rpi_image_name) -f Dockerfile-rpi .

push:
	docker tag -f $(image_name) $(registry)/$(image_name)
	docker push $(registry)/$(image_name)

push-rpi:
	docker tag -f $(rpi_image_name) $(registry)/$(rpi_image_name)
	docker push $(registry)/$(rpi_image_name)

pull:
	docker pull $(registry)/$(image_name)
	docker tag $(registry)/$(image_name) $(image_name)

pull-rpi:
	docker pull $(registry)/$(rpi_image_name)
	docker tag $(registry)/$(rpi_image_name) $(rpi_image_name)

run-bash:
	docker run -it --net=$(network_name) --rm -v /media/data/Informatique/Python/Netcall/netcall:/usr/src/netcall $(image_name) bash

run:
	docker run -it --net=$(network_name) --rm $(image_name) python -m isac_cmd hello

run1:
	docker run -it --net=$(network_name) --rm $(image_name) python -m isac_cmd gdsjkl01 # test01 gdsjkl01

run1-rpi:
	docker run -it --net=$(network_name) --rm $(rpi_image_name) python -m isac_cmd gdsjkl01 # test01 gdsjkl01

run2:
	docker run -it --net=$(network_name) --rm $(image_name) python -m isac_cmd fdsfds02 # test02 fdsfds02

run2-rpi:
	docker run -it --net=$(network_name) --rm $(rpi_image_name) python -m isac_cmd fdsfds02 # test02 fdsfds02

run3:
	docker run -it --net=$(network_name) --rm $(image_name) python -i isac.py test03

test1:
	docker run -it --net=$(network_name) --rm $(image_name) python test.py test01

test2:
	docker run -it --net=$(network_name) --rm $(image_name) python test.py test02
