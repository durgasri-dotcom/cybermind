 -- CVE analytics summary mart

with cves as (
    select * from {{ ref('stg_cves') }}
),

summary as (
    select
        severity_band,
        risk_band,
        ingested_date,
        count(*) as total_cves,
        avg(cvss_score) as avg_cvss_score,
        max(cvss_score) as max_cvss_score,
        avg(risk_score) as avg_risk_score,
        count(*) filter (where cvss_score >= 9.0) as critical_count,
        count(*) filter (where cvss_score >= 7.0 and cvss_score < 9.0) as high_count,
        count(*) filter (where cvss_score >= 4.0 and cvss_score < 7.0) as medium_count
    from cves
    group by severity_band, risk_band, ingested_date
)

select * from summary