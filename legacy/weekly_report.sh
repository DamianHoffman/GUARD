#!/bin/bash
# DO NOT RUN. Deliberately flawed example. See docs/legacy-audit.md
export PGPASSWORD='Haslo123!'
psql -U postgres -h localhost guard -c "COPY (SELECT * FROM campaigns c JOIN daily_perf d ON d.camp=c.id) TO '/tmp/report.csv' CSV HEADER"
echo "done"
