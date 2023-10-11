#!/bin/bash

PROJECT=llx-upgrade-release
PYTHON_FILES="../src/*.py"

mkdir -p $PROJECT
xgettext $PYTHON_FILES -o ${PROJECT}/${PROJECT}.pot

