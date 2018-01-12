#!/bin/sh
faas remove -f ./colorizationk.yml
faas build -f ./colorization.yml
faas push -f ./colorization.yml
faas deploy -f ./colorization.yml --replace -e read_timeout=60,write_timeout=60
