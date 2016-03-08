import boto3
from gzip_reader import GzipReader


s3 = boto3.resource("s3")


def s3_open(bucket, key, use_gzip=False):
    """Open and return a s3 object"""
    obj = s3.Object(bucket, key)
    result = obj.get()
    body = result["Body"]
    gzip_header = "ContentEncoding" in result and \
        "gzip" in result["ContentEncoding"]
    if use_gzip or key.endswith(".gz") or gzip_header:
        return GzipReader(body, blocksize=16*1024)
    else:
        return body
