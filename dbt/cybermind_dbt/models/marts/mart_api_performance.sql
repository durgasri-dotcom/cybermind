-- API performance analytics mart
-- Tracks endpoint performance and error rates

with logs as (
    select * from {{ ref('stg_request_logs') }}
),

performance as (
    select
        path,
        method,
        request_date,
        count(*) as total_requests,
        avg(latency_ms) as avg_latency_ms,
        min(latency_ms) as min_latency_ms,
        max(latency_ms) as max_latency_ms,
        count(*) filter (where status_category = 'SUCCESS') as success_count,
        count(*) filter (where status_category = 'SERVER_ERROR') as error_count,
        round(
            count(*) filter (where status_category = 'SUCCESS')::numeric /
            nullif(count(*), 0) * 100, 2
        ) as success_rate_pct,
        count(*) filter (where latency_category = 'VERY_SLOW') as slow_requests
    from logs
    group by path, method, request_date
)

select * from performance
