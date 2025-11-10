#!/bin/bash
# Test script for Neural Dive

echo "Testing Neural Dive basic functionality..."
echo ""

# Test 1: Basic movement
echo "=== Test 1: Move right 10 times ==="
cat <<EOF | ./neural_dive.py --test
right
right
right
right
right
right
right
right
right
right
EOF

echo ""
echo "=== Test 2: Try to walk through wall ==="
cat <<EOF | ./neural_dive.py --test
up
up
up
up
up
EOF

echo ""
echo "=== Test 3: Move to NPC and interact ==="
cat <<EOF | ./neural_dive.py --test
right
right
right
right
right
right
right
right
right
right
down
down
down
interact
EOF

echo ""
echo "All tests complete!"
