#!/bin/bash

SPHINXOPTS=
SPHINXBUILD=sphinx-build
SOURCEDIR=doc
BUILDDIR=build

if [[ ! -e "$SOURCEDIR/conf.py" ]]; then
    echo "Please run me from the repository's base directory"
    exit 1
fi

sphinx-build -M html "$SOURCEDIR" "$BUILDDIR" $SPHINXOPTS

