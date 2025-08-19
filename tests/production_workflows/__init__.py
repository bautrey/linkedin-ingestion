"""
Production workflow tests - these are slow tests that validate end-to-end workflows.

These tests:
- Actually call production endpoints with real data
- Wait for async jobs to complete (2-5 minutes per test)
- Validate full user workflows end-to-end
- Should be run separately from fast unit tests

Run with: pytest tests/production_workflows/ -v --timeout=300
"""
