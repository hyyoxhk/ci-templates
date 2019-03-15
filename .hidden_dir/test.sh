#!/bin/bash

set -e
set -x

echo script called with \'$@\'
touch $@
