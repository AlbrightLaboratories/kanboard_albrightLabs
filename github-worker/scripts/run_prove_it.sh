#!/bin/bash
# run_prove_it.sh - Execute prove-it validation on target repository
# Implements GW-03: prove-it script runs test suite, captures exit code
#
# This script:
# 1. Detects the project type (Python, Node, etc.)
# 2. Runs the appropriate test suite
# 3. Checks coverage thresholds
# 4. Verifies modularity constraints
# 5. Returns exit code (0=pass, non-zero=fail)

set -e

echo "=== prove-it validation starting ==="
echo "Working directory: $(pwd)"
echo "Date: $(date)"

FAILURES=()
WARNINGS=()

# Function to add failure
add_failure() {
    FAILURES+=("$1")
    echo "FAILURE: $1"
}

# Function to add warning
add_warning() {
    WARNINGS+=("$1")
    echo "WARNING: $1"
}

# Detect project type and run tests
run_tests() {
    echo ""
    echo "=== Running test suite ==="

    # Python (pytest)
    if [ -f "pytest.ini" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ] || [ -d "tests" ]; then
        echo "Detected Python project"
        if command -v pytest &> /dev/null; then
            pytest --tb=short -v 2>&1 || {
                add_failure "pytest failed with exit code $?"
                return 1
            }
        else
            echo "pytest not found, trying unittest"
            python -m unittest discover -v 2>&1 || {
                add_failure "unittest failed with exit code $?"
                return 1
            }
        fi
        return 0
    fi

    # Node.js (npm test)
    if [ -f "package.json" ]; then
        echo "Detected Node.js project"
        if grep -q '"test"' package.json; then
            npm test 2>&1 || {
                add_failure "npm test failed with exit code $?"
                return 1
            }
        else
            echo "No test script in package.json"
            add_warning "No test script defined in package.json"
        fi
        return 0
    fi

    # Rust (cargo test)
    if [ -f "Cargo.toml" ]; then
        echo "Detected Rust project"
        cargo test 2>&1 || {
            add_failure "cargo test failed with exit code $?"
            return 1
        }
        return 0
    fi

    # Go (go test)
    if [ -f "go.mod" ]; then
        echo "Detected Go project"
        go test ./... 2>&1 || {
            add_failure "go test failed with exit code $?"
            return 1
        }
        return 0
    fi

    echo "No recognized test framework found"
    add_warning "No test framework detected"
    return 0
}

# Check modularity constraints
check_modularity() {
    echo ""
    echo "=== Checking modularity constraints ==="

    # Check for files > 200 LOC (excluding tests, config, generated)
    LARGE_FILES=$(find . -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
        grep -v node_modules | \
        grep -v __pycache__ | \
        grep -v ".test." | \
        grep -v ".spec." | \
        grep -v "test_" | \
        xargs wc -l 2>/dev/null | \
        awk '$1 > 200 && $2 != "total" {print $2 " (" $1 " lines)"}' || true)

    if [ -n "$LARGE_FILES" ]; then
        add_warning "Files exceeding 200 LOC:\n$LARGE_FILES"
    else
        echo "All files within 200 LOC limit"
    fi
}

# Check for coverage report
check_coverage() {
    echo ""
    echo "=== Checking coverage ==="

    # Check if coverage exists
    if [ -f ".coverage" ] || [ -f "coverage.xml" ] || [ -d "coverage" ] || [ -d "htmlcov" ]; then
        echo "Coverage data found"

        # Try to extract coverage percentage
        if command -v coverage &> /dev/null && [ -f ".coverage" ]; then
            COVERAGE_PCT=$(coverage report | grep TOTAL | awk '{print $NF}' | tr -d '%')
            if [ -n "$COVERAGE_PCT" ] && [ "$COVERAGE_PCT" -lt 70 ]; then
                add_warning "Coverage is ${COVERAGE_PCT}%, below 70% threshold"
            else
                echo "Coverage: ${COVERAGE_PCT}%"
            fi
        fi
    else
        echo "No coverage data found (optional)"
    fi
}

# Main execution
main() {
    echo "Starting prove-it validation..."

    # Run tests
    run_tests
    TEST_RESULT=$?

    # Check modularity
    check_modularity

    # Check coverage (optional)
    check_coverage

    echo ""
    echo "=== Validation Summary ==="
    echo "Failures: ${#FAILURES[@]}"
    echo "Warnings: ${#WARNINGS[@]}"

    if [ ${#FAILURES[@]} -gt 0 ]; then
        echo ""
        echo "FAILURES:"
        for f in "${FAILURES[@]}"; do
            echo "  - $f"
        done
        echo ""
        echo "=== prove-it FAILED ==="
        exit 1
    fi

    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo ""
        echo "WARNINGS (non-blocking):"
        for w in "${WARNINGS[@]}"; do
            echo "  - $w"
        done
    fi

    echo ""
    echo "=== prove-it PASSED ==="
    exit 0
}

main "$@"
