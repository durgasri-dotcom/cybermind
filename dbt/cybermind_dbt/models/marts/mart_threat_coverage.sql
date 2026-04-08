-- Threat coverage analytics mart
-- Shows MITRE ATT&CK technique coverage across CVEs and alerts

with cves as (
    select * from {{ ref('stg_cves') }}
),

alerts as (
    select * from {{ ref('stg_alerts') }}
),

alert_summary as (
    select
        threat_id,
        count(*) as alert_count,
        avg(priority_score) as avg_priority,
        max(priority_score) as max_priority,
        count(*) filter (where status = 'resolved') as resolved_count,
        avg(resolution_hours) as avg_resolution_hours
    from alerts
    group by threat_id
),

coverage as (
    select
        a.threat_id,
        a.alert_count,
        a.avg_priority,
        a.max_priority,
        a.resolved_count,
        a.avg_resolution_hours,
        case
            when a.max_priority = 4 then 'CRITICAL'
            when a.max_priority = 3 then 'HIGH'
            when a.max_priority = 2 then 'MEDIUM'
            else 'LOW'
        end as threat_level
    from alert_summary a
)

select * from coverage
