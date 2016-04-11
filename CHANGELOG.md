<a name="0.4"></a>
## 0.4 (2016-04-11)


#### Features

*   refactor to use only Redis ([2503a9ee](https://github.com/mozilla-services/push-processor/commit/2503a9eeb8202dd716e266c8227448fef3ca0558), closes [#11](https://github.com/mozilla-services/push-processor/issues/11))



<a name="0.3"></a>
## 0.3 (2016-04-07)


#### Bug Fixes

*   use new correct location for jwt_crypto_key ([6641fa8c](https://github.com/mozilla-services/push-processor/commit/6641fa8c9d58d302823c793dfcbef8897e8553ce))



<a name="0.2"></a>
## 0.2 (2016-04-04)


#### Features

*   read processor settings from root of s3 dir ([87509331](https://github.com/mozilla-services/push-processor/commit/875093313f3fa07b242e73df72465c0ba280862c), closes [#8](https://github.com/mozilla-services/push-processor/issues/8))
*   add lambda bundling and config ([1daadc57](https://github.com/mozilla-services/push-processor/commit/1daadc57b31521257cbf7dc281d271a089963346), closes [#4](https://github.com/mozilla-services/push-processor/issues/4))



<a name="0.1"></a>
## 0.1 (2016-03-22)


#### Features

*   refactor handler into singleton class ([ba2666c4](https://github.com/mozilla-services/push-processor/commit/ba2666c439eb920a6fa70ad180a40bd533019d15))
*   add db and lambda handler ([8061cee0](https://github.com/mozilla-services/push-processor/commit/8061cee0f0b8d3461d2c8466dd2300705c262999))
*   add public key processor ([de1cc485](https://github.com/mozilla-services/push-processor/commit/de1cc48550a501947fde2bfcc2aa78d6fcd2d7b4))
*   add aws s3 open function with streaming reader ([3bdf30f7](https://github.com/mozilla-services/push-processor/commit/3bdf30f75e164dbbb5e19d4ac3a7b9074f199245))
*   add heka protobuf stream decoding to message ([bb23b722](https://github.com/mozilla-services/push-processor/commit/bb23b7220c9885ccaa9b0067f1d469b48b9af1f6))

#### Chore

*   add push message dep ([6aae9683](https://github.com/mozilla-services/push-processor/commit/6aae96830db5622884820c1e5e920bee5cdff08c))
*   add requirements.txt ([e1c35e80](https://github.com/mozilla-services/push-processor/commit/e1c35e80ebc353bf817712ac7cea7b75201b1d26))
*   initial project setup ([da373233](https://github.com/mozilla-services/push-processor/commit/da373233237e8e641cbc265bdc30043885bdfb11))
*   add license file ([1849f17c](https://github.com/mozilla-services/push-processor/commit/1849f17c13ed9979a800964541e2b34112aa8c20))
