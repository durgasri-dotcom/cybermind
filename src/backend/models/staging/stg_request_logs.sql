-- Staging model for API request logs

with source as (
    select * from public.request_logs
),

staged as (
    select
        id,
        method,
        path,
        status_code,
        latency_ms,
        client_ip,
        timestamp,
        case
            when status_code between 200 and 299 then 'SUCCESS'
            when status_code between 300 and 399 then 'REDIRECT'
            when status_code between 400 and 499 then 'CLIENT_ERROR'
            when status_code between 500 and 599 then 'SERVER_ERROR'
            else 'UNKNOWN'
        end as status_category,
        case
            when latency_ms < 100  then 'FAST'
            when latency_ms < 500  then 'NORMAL'
            when latency_ms < 2000 then 'SLOW'
            else 'VERY_SLOW'
        end as latency_category,
        date_trunc('hour', timestamp) as request_hour,
        date_trunc('day', timestamp) as request_date
    from source
)

select * from staged