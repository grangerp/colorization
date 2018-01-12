#!/bin/sh
faas remove -f ./colorizationwebhook.yml
faas build -f ./colorizationwebhook.yml
faas push -f ./colorizationwebhook.yml
faas deploy -f ./colorizationwebhook.yml
