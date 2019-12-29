# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import os
import setuptools

# Third-party imports

# Local imports


base_folder = os.path.dirname(os.path.abspath(__file__))

readme_file = os.path.join(base_folder, 'README.md')
with open(readme_file, 'r') as fh:
    long_description = fh.read()

req_file = os.path.join(base_folder, 'requirements.txt')
with open(req_file, 'r') as fh:
    install_requires = fh.read().splitlines()


setup_args = dict(
    name='alidron-isac',
    version='0.2',
    author='Axel Voitier',
    author_email='axel.voitier@gmail.com',
    description='Alidron ISAC',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/Alidron/alidron-isac',
    packages=setuptools.find_packages(),
    # install_requires=install_requires,
    tests_require=[
        'pytest',
    ],
    python_requires='~=3.8',
    classifiers=(
        'Framework :: Alidron',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3 :: Only',
    )
)


if __name__ == '__main__':
    setuptools.setup(**setup_args)
