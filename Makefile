SHELL := /bin/sh
APPNAME = push_messages
HERE = $(shell pwd)

.PHONY: all travis lambda-package

all:	travis

travis:
	pip install tox

$(HERE)/lenv:
	virtualenv lenv
	$(HERE)/lenv/bin/pip install -r lambda-requirements.txt
	echo "#" > lenv/lib/python2.7/site-packages/zope/__init__.py
	echo "#" > lenv/lib/python2.7/site-packages/google/__init__.py
	$(HERE)/lenv/bin/python setup.py develop

lambda-package: $(HERE)/lenv
	virtualenv ppenv
	$(HERE)/ppenv/bin/pip install lambda-uploader
	rm -rf lenv/lib/python2.7/site-packages/pip*
	rm -rf lenv/lib/python2.7/site-packages/twisted/trial
	rm -rf lenv/lib/python2.7/site-packages/twisted/web
	rm -rf lenv/lib/python2.7/site-packages/twisted/words
	rm -rf lenv/lib/python2.7/site-packages/twisted/conch
	rm -rf lenv/lib/python2.7/site-packages/twisted/internet
	rm -rf lenv/lib/python2.7/site-packages/twisted/mail
	rm -rf lenv/lib/python2.7/site-packages/twisted/test
	$(HERE)/ppenv/bin/lambda-uploader --virtualenv=lenv --no-upload

docker-lambda-package:
	docker run -it --rm -v "$(HERE)":/app python:2.7 /bin/bash -c 'cd /app; make lambda-package'
