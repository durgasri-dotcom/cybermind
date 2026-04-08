-- Staging model for security alerts

with source as (
    select * from public.alerts
),

staged as (
    select
        id,
        threat_id,
        title,
        description,
        priority,
        status,
        source_ip,
        target_asset,
        triggered_at,
        resolved_at,
        case
            when priority = 'P1' then 4
            when priority = 'P2' then 3
            when priority = 'P3' then 2
            when priority = 'P4' then 1
            else 0
        end as priority_score,
        case
            when resolved_at is not null
            then extract(epoch from (resolved_at - triggered_at)) / 3600
            else null
        end as resolution_hours,
        date_trunc('day', triggered_at) as alert_date
    from source
)

select * from staged