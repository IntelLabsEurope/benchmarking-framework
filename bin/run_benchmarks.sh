#!/bin/bash

rm -f nohup.out
sleep 2
nohup python experimental_framework/VNFBench.py &
sleep 2
tail -f nohup.out
