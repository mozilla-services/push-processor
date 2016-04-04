SHELL := /bin/sh
APPNAME = push_messages
HERE = $(shell pwd)

.PHONY: all travis lambda-package

all:	travis

travis: $(HERE)/ddb
	pip install tox

$(HERE)/ddb:
	mkdir $@
	curl -sSL http://dynamodb-local.s3-website-us-west-2.amazonaws.com/dynamodb_local_latest.tar.gz | tar xzvC $@

$(HERE)/lenv:
	virtualenv lenv
	$(HERE)/lenv/bin/pip install -r lambda-requirements.txt
	echo "#" > lenv/lib/python2.7/site-packages/zope/__init__.py
	echo "#" > lenv/lib/python2.7/site-packages/google/__init__.py
	$(HERE)/lenv/bin/python setup.py develop

lambda-package: $(HERE)/lenv
	pip install lambda-uploader
	rm -rf lenv/lib/python2.7/site-packages/pip*
	rm -rf lenv/lib/python2.7/site-packages/twisted/trial
	rm -rf lenv/lib/python2.7/site-packages/twisted/web
	rm -rf lenv/lib/python2.7/site-packages/twisted/words
	rm -rf lenv/lib/python2.7/site-packages/twisted/conch
	rm -rf lenv/lib/python2.7/site-packages/twisted/internet
	rm -rf lenv/lib/python2.7/site-packages/twisted/mail
	rm -rf lenv/lib/python2.7/site-packages/twisted/test
	$(HERE)/ppenv/bin/lambda-uploader --virtualenv=lenv --no-upload
