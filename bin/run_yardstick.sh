#!/bin/bash

rm -f nohup.out
sleep 2
nohup python yardstick_simulator.py &
sleep 2
tail -f nohup.out