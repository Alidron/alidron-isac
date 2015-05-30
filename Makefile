image_name = alidron/alidron-isac

.PHONY: clean clean-dangling build run-bash run1 run2 run3 test1 test2

clean:
	docker rmi $(image_name) || true

clean-dangling:
	docker rmi $(docker images -q -f dangling=true) || true

build: clean-dangling
	docker build --force-rm=true -t $(image_name) .

run-bash:
	docker run -it --rm -v /media/data/Informatique/Python/Netcall/netcall:/usr/src/netcall $(image_name) bash

run:
	docker run -it --rm $(image_name) python -m isac_cmd hello

run1:
	docker run -it --rm $(image_name) python -m isac_cmd gdsjkl01 # test01 gdsjkl01

run2:
	docker run -it --rm $(image_name) python -m isac_cmd fdsfds02 # test02 fdsfds02

run3:
	docker run -it --rm $(image_name) python -i isac.py test03

test1:
	docker run -it --rm $(image_name) python test.py test01

test2:
	docker run -it --rm $(image_name) python test.py test02
