#!/bin/bash
# Script to organize test results and clean up the repository

# Create test result directories if they don't exist
mkdir -p /workspaces/Elson/test_results/beta
mkdir -p /workspaces/Elson/test_results/hybrid_model
mkdir -p /workspaces/Elson/test_results/quantum_model

# Move beta test results
echo "Moving beta test results..."
find /workspaces/Elson -name "beta_test_results_*" -type d -maxdepth 1 -exec mv {} /workspaces/Elson/test_results/beta/ \;

# Move hybrid model test results
echo "Moving hybrid model test results..."
find /workspaces/Elson -name "hybrid_model_*" -type d -maxdepth 1 -exec mv {} /workspaces/Elson/test_results/hybrid_model/ \;
find /workspaces/Elson -name "win_rate_results" -type d -maxdepth 1 -exec mv {} /workspaces/Elson/test_results/hybrid_model/ \;

# Move quantum model test results
echo "Moving quantum model test results..."
find /workspaces/Elson -name "quantum_model_test_results" -type d -maxdepth 1 -exec mv {} /workspaces/Elson/test_results/quantum_model/ \;

# Clean up log files
echo "Archiving log files..."
mkdir -p /workspaces/Elson/test_results/logs
find /workspaces/Elson -name "*.log" -type f -maxdepth 1 -exec mv {} /workspaces/Elson/test_results/logs/ \;

echo "Test results organization complete!"