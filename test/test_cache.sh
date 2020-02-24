#!/bin/bash

set -x

ls /cache

if [ -e /cache/foo-$1 ]
then
  uname -a | tee /cache/bar-$1
else
  echo /cache/foo-$1 not available, failed to mount /cache
  exit 1
fi
