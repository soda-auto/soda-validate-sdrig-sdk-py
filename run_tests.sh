#!/bin/bash
# Run all SDRIG SDK tests

set -e

echo "========================================"
echo "SDRIG SDK - Test Runner"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install -r requirements-test.txt"
    exit 1
fi

# Parse arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-no}"

echo "Test type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo ""

# Run unit tests
if [ "$TEST_TYPE" == "unit" ] || [ "$TEST_TYPE" == "all" ]; then
    echo -e "${YELLOW}Running Unit Tests...${NC}"
    echo "========================================"
    if [ "$COVERAGE" == "coverage" ]; then
        pytest tests/unit/ -v --cov=sdrig --cov-report=term-missing --cov-report=html
    else
        pytest tests/unit/ -v
    fi
    UNIT_EXIT=$?
    echo ""
fi

# Run integration tests (optional, requires hardware)
if [ "$TEST_TYPE" == "integration" ] || [ "$TEST_TYPE" == "all" ]; then
    echo -e "${YELLOW}Running Integration Tests (requires hardware)...${NC}"
    echo "========================================"
    echo "Note: Integration tests require actual hardware"
    echo "Skipping... (run manually with: python3 tests/test_integration_all_messages.py)"
    echo ""
fi

# Run compliance tests (optional, requires hardware)
if [ "$TEST_TYPE" == "compliance" ] || [ "$TEST_TYPE" == "all" ]; then
    echo -e "${YELLOW}Running Compliance Tests (requires hardware)...${NC}"
    echo "========================================"
    echo "Note: Compliance tests require actual hardware"
    echo "Skipping... (run manually with: python3 tests/test_official_manual_compliance.py)"
    echo ""
fi

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"

if [ "$TEST_TYPE" == "unit" ] || [ "$TEST_TYPE" == "all" ]; then
    if [ $UNIT_EXIT -eq 0 ]; then
        echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
    else
        echo -e "${RED}✗ Unit Tests: FAILED${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}All tests completed successfully!${NC}"

# Show coverage report location if generated
if [ "$COVERAGE" == "coverage" ]; then
    echo ""
    echo "Coverage report: htmlcov/index.html"
    echo "View with: xdg-open htmlcov/index.html"
fi
