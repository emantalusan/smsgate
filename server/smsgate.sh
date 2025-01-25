#!/bin/sh

my_dir="$(dirname "$0")"
cd "${my_dir}"

cd /opt/smsgate
. ./venv/bin/activate
./server/smsgate.py
