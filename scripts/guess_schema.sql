SELECT
    column_name,
    column_type,
    (
        CASE
        WHEN column_type = 'VARCHAR' THEN
        (
            CASE
            WHEN approx_unique > 1 AND approx_unique <= 50
            THEN 'NOMINAL'
            ELSE 'IGNORE'
            END
        )
        WHEN column_type = 'DOUBLE' THEN
        (
            -- Not enough unique values. Better off modeling as nominal.
            CASE
            WHEN approx_unique < 20
            OR (approx_unique / count) < 0.02
            THEN 'NOMINAL'

            -- Consecutive numbers -- probably an ID?
            WHEN approx_unique = count
            AND count = TRY_CAST(min AS INTEGER) - TRY_CAST(max AS INTEGER) + 1
            THEN 'IGNORE'

            ELSE 'NUMERICAL'
            END
        )
        END
    ) AS column_statistical_type,
    (
        CASE
        WHEN column_statistical_type = 'IGNORE' THEN 'ignore'
        WHEN column_statistical_type = 'NOMINAL' THEN 'categorical'
        WHEN column_statistical_type = 'NUMERICAL' THEN 'normal'
        END
    ) AS column_cgpm_statistical_type,
    (
        CASE
        WHEN column_statistical_type = 'NOMINAL' THEN 'dd'
        WHEN column_statistical_type = 'NUMERICAL' THEN 'nich'
        END
    ) AS loom_statistical_type,
FROM read_csv_auto('/dev/stdin', header=true)
