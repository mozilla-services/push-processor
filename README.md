# Push Processors

Mozilla Push message log processors. These processors can be run under AWS
Lambda or deployed to a machine. This project also contains common helper
functions for parsing heka protobuf messages and running in AWS Lambda.

Currently this consists of a single processor for the Push Messages API.

## Push Message Processor

Processes push log messages to extract message metadata for registered crypto
public-keys.

Requires DynamoDB and Redis.

## Developing

Checkout this repo, you will need Redis installed and a local DynamoDB to test
against.

Then:

    $ virtualenv ppenv
    $ source ppenv/bin/activate
    $ pip install -r requirements.txt
    $ python setup.py develop
