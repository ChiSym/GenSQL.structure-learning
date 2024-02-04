#!/usr/bin/env bash
columns=$(
duckdb -noheader -list :memory: <<-EOF | paste -s -d , -
    SELECT column_name
    FROM read_csv_auto('data/schema.csv', header=true)
    WHERE column_statistical_type != 'IGNORE'
EOF
)
duckdb -csv :memory: "SELECT $columns FROM read_csv_auto('/dev/stdin', header=true)"
