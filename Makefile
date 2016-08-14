all:
	@echo "do nothing"

clean:
	rm -f `find . -type f -name '*.py[co]' `
	rm -fr dist
	rm -fr  exception_mail.egg-info 

build: clean
	python setup.py sdist

install: build
	cd dist && mkdir exception_mail && tar zxf *.tar.gz -C ./exception_mail --strip-components 1 && cd -
	virtualenv --no-site-packages dist/tmp
	. dist/tmp/bin/activate && cd dist/exception_mail && python setup.py build && python setup.py install && cd -

.PHONY : all clean build
