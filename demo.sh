#!/bin/bash
# Demo script showing job scheduler capabilities

echo "=== Job Scheduler Demo ==="
echo

echo "1. Validating example configuration..."
job-scheduler validate examples/simple-job.json
echo

echo "2. Running a single job directly..."
job-scheduler run-single "demo-job" "https://github.com/octocat/Hello-World.git" "master" "echo 'Demo completed!' && ls -la README"
echo

echo "3. Running multiple jobs from configuration..."
job-scheduler run examples/multi-job-test.yml --sequential
echo

echo "Demo completed!"