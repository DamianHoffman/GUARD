#!/bin/bash
# DO NOT RUN. Deliberately flawed example. See docs/legacy-audit.md
# jan's backup script
pg_dump -U postgres -h localhost guard > /var/backups/guard.sql
# TODO: delete old ones
cp /var/backups/guard.sql /var/backups/guard_$(date +%d%m).sql
