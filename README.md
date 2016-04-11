[![codecov.io](https://codecov.io/github/mozilla-services/push-processor/coverage.svg?branch=master)](https://codecov.io/github/mozilla-services/push-processor?branch=master) [![Build Status](https://travis-ci.org/mozilla-services/push-processor.svg?branch=master)](https://travis-ci.org/mozilla-services/push-processor)

# Push Processors

Mozilla Push message log processors. These processors can be run under AWS
Lambda or deployed to a machine. This project also contains common helper
functions for parsing heka protobuf messages and running in AWS Lambda.

Currently this consists of a single processor for the Push Messages API.

## Push Message Processor

Processes push log messages to extract message metadata for registered crypto
public-keys.

Requires Redis.

## Developing

Checkout this repo, you will need Redis installed to test against.

Then:

    $ virtualenv ppenv
    $ source ppenv/bin/activate
    $ pip install -r requirements.txt
    $ python setup.py develop

## Creating an AWS Lambda Zipfile

After modifying ``push_processor/settings.js`` for your appropriate settings, a
Lambda-ready zipfile can be created with make:

    $ make lambda-package

All files in the work directory are included except files listed in the
``ignore`` section of ``lambda.json``. Remove any other files that should not
be included in the zipfile from the work directory.

The AWS handler you should set is: ``lambda.handler``, which will then call
the Push Processor.
