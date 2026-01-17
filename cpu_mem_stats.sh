#!/usr/bin/env bash
#
# Collects and displays CPU and memory usage statistics.
# 
# Requirements:
#   - sysstat (for mpstat)
#   - procps  (for free)

echo "--- CPU ---"
mpstat 1 1 | tail -n 1 | awk '{print "Usage: " 100-$NF "%"}'
echo "--- Memory ---"
free -h | grep Mem | awk '{print "Total: " $2 "  Used: " $3 "  Free: " $4}'
