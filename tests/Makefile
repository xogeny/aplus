all:	test

env:	env/bin/activate

env/bin/activate: requirements.txt
	test -d env || virtualenv --no-site-packages env
	. env/bin/activate; pip install -r requirements.txt
	touch env/bin/activate

install:	env
	. env/bin/activate; (cd ..; python setup.py install)

test:	install
	. env/bin/activate; nosetests -s --with-coverage --cover-package=aplus .
