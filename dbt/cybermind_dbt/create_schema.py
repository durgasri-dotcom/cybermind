
schema = '''version: 2

models:
  - name: stg_cves
    description: Staged CVE data from NVD with severity and risk bands
    columns:
      - name: id
        data_tests:
          - not_null
          - unique
      - name: cve_id
        data_tests:
          - not_null
          - unique
      - name: severity_band
        data_tests:
          - not_null
          - accepted_values:
              values: [CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN]

  - name: stg_alerts
    description: Staged security alerts with priority scores
    columns:
      - name: id
        data_tests:
          - not_null
          - unique

  - name: stg_request_logs
    description: Staged API request logs with latency categories
    columns:
      - name: id
        data_tests:
          - not_null
          - unique
      - name: status_category
        data_tests:
          - not_null
          - accepted_values:
              values: [SUCCESS, CLIENT_ERROR, SERVER_ERROR, OTHER]
'''
open('models/staging/schema.yml', 'w').write(schema)
print('schema.yml created!')

