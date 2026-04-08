
import os

stg_alerts = '''with source as (select * from public.alerts),
staged as (
    select id, threat_id, title, description, priority, status,
        source_ip, target_asset, triggered_at, resolved_at,
        case when priority = 'P1' then 4 when priority = 'P2' then 3
             when priority = 'P3' then 2 when priority = 'P4' then 1 else 0
        end as priority_score,
        case when resolved_at is not null
             then extract(epoch from (resolved_at - triggered_at)) / 3600
             else null end as resolution_hours,
        date_trunc('day', triggered_at) as alert_date
    from source)
select * from staged'''

stg_logs = '''with source as (select * from public.request_logs),
staged as (
    select id, method, path, status_code, latency_ms, client_ip, timestamp,
        case when status_code between 200 and 299 then 'SUCCESS'
             when status_code between 400 and 499 then 'CLIENT_ERROR'
             when status_code between 500 and 599 then 'SERVER_ERROR'
             else 'OTHER' end as status_category,
        case when latency_ms < 100 then 'FAST'
             when latency_ms < 500 then 'NORMAL'
             when latency_ms < 2000 then 'SLOW'
             else 'VERY_SLOW' end as latency_category,
        date_trunc('hour', timestamp) as request_hour,
        date_trunc('day', timestamp) as request_date
    from source)
select * from staged'''

mart_cve = '''with cves as (select * from {{ ref('stg_cves') }}),
summary as (
    select severity_band, risk_band, ingested_date,
        count(*) as total_cves,
        avg(cvss_score) as avg_cvss_score,
        max(cvss_score) as max_cvss_score,
        avg(risk_score) as avg_risk_score,
        count(*) filter (where cvss_score >= 9.0) as critical_count,
        count(*) filter (where cvss_score >= 7.0 and cvss_score < 9.0) as high_count,
        count(*) filter (where cvss_score >= 4.0 and cvss_score < 7.0) as medium_count
    from cves
    group by severity_band, risk_band, ingested_date)
select * from summary'''

os.makedirs('models/staging', exist_ok=True)
os.makedirs('models/marts', exist_ok=True)
open('models/staging/stg_alerts.sql', 'w').write(stg_alerts)
open('models/staging/stg_request_logs.sql', 'w').write(stg_logs)
open('models/marts/mart_cve_summary.sql', 'w').write(mart_cve)
print('All models created!')

