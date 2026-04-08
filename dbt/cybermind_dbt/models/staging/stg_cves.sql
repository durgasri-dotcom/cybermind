-- Staging model for CVEs from NVD
-- Normalizes raw CVE data for downstream analytics

with source as (
    select * from public.cves
),

staged as (
    select
        id,
        cve_id,
        description,
        cvss_score,
        cvss_severity,
        cvss_vector,
        published_date,
        modified_date,
        risk_score,
        ingested_at,
        case
            when cvss_score >= 9.0 then 'CRITICAL'
            when cvss_score >= 7.0 then 'HIGH'
            when cvss_score >= 4.0 then 'MEDIUM'
            when cvss_score > 0    then 'LOW'
            else 'UNKNOWN'
        end as severity_band,
        case
            when risk_score >= 0.85 then 'CRITICAL'
            when risk_score >= 0.65 then 'HIGH'
            when risk_score >= 0.40 then 'MEDIUM'
            else 'LOW'
        end as risk_band,
        date_trunc('day', ingested_at) as ingested_date
    from source
)

select * from staged
