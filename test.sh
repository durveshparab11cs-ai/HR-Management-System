#!/bin/bash
echo "Testing coordinator API..."
curl -X POST http://localhost:8000/coordinator/api/search-employee \
  -H "Content-Type: application/json" \
  -d '{"employee_code":"E-2512012"}' \
  -w "\nStatus: %{http_code}\n"
