#! /usr/bin/env bash

window=$1
char="$2"

# type --window didn't work with signal and terminal but did work with
# emacs and browser (emacs for sure)
# so activating the window first
xdotool windowactivate $window

# tried to debug this and it seems my echo was enough to make
# the bug go away so just waiting a split second
sleep .1
xdotool type "$char"
