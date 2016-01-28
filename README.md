Alidron ISAC
============

[![build status](https://git.tinigrifi.org/ci/projects/1/status.png?ref=master)](https://git.tinigrifi.org/ci/projects/1?ref=master) [![Gitter](https://badges.gitter.im/gitterHQ/gitter.svg)](https://gitter.im/Alidron/talk)

* **I**nstrumentation
* **S**upervision
* **A**nalysis
* **C**ontrol

This is currently the core of Alidron project. It is the network, the fabric embodying the main concepts of Alidron.

This is an exploration version of these concepts. It is made in Python to be able to develop and iterate quickly. In the future other languages will be supported (target: a "VM" (Java/JVM, Mono/.Net, LLVM), a compiled and static form (C/C++, Go or Rust), a scripting language (Python, Javascript)).

Docker containers
=================

The Docker images are accessible on:
* x86: [alidron/alidron-isac](https://hub.docker.com/r/alidron/alidron-isac/)
* ARM/Raspberry Pi: [alidron/rpi-alidron-isac](https://hub.docker.com/r/alidron/rpi-alidron-isac/)

Dockerfiles are accessible from the Github repository:
* x86: [Dockerfile](https://github.com/Alidron/alidron-isac/blob/master/Dockerfile)
* ARM/Raspberry Pi: [Dockerfile](https://github.com/Alidron/alidron-isac/blob/master/Dockerfile-rpi)

Give it a try
=============

The natural way of running an Isac node is with its Docker containers.
```
$ docker pull alidron/alidron-isac
$ docker run -it --rm alidron/alidron-isac python
```
On the Python prompt, do:
```
from isac import IsacNode, IsacValue

my_node = IsacNode('node1')

my_iv = IsacValue(
    my_node,
    'test://my_application/a_value', # Value name, by convention a URI. You are free to give it whatever scheme, authority and path
    initial_value=1, # Optional
    survey_last_value=False, # We know it is the first value for this URI
    survey_static_tags=False # Faster initialisation if you don't need static tags
)

def callback(iv, value, timestamp, tags):
    print 'Received update on %s at %s: %s' % (iv.uri, str(timestamp), str(value))

my_iv.observers += callback # observers is a set()

my_node.serve_forever() # Block
```

In another terminal, open another node:
```
$ docker run -it --rm alidron/alidron-isac python
```
And type the following at the Python prompt:
```
from isac import IsacNode, IsacValue

my_node = IsacNode('node2')

my_iv = IsacValue(my_node, 'test://my_application/a_value')

print my_iv.value, my_iv.timestamp

my_iv.value += 1 # value is a property with getter and setter
```
With that last command you should have seen the update arrive in the first console.

To close the nodes you need to call `my_node.shutdown()` before quitting as usual the Python prompt (Ctrl+D). With the first node, as it is serving forever you need to do a Ctrl+C first.

You can also try this over multiple host. Just configure your Docker services to use [multi-host networking](https://docs.docker.com/engine/userguide/networking/get-started-overlay/). Alternatively, you can also use the option `--net=host` with the run commands if the hosts are on the same network. It is easier but less "contained" ;-).

More documentation will come later :-). Meanwhile, you can read the code, the tests, [the other projects](https://github.com/Alidron), and come discuss on the [Gitter channel](https://gitter.im/Alidron/talk).

License and contribution policy
===============================

This project is licensed under LGPLv3.

To contribute, please, follow the [C4.1](http://rfc.zeromq.org/spec:22) contribution policy.
