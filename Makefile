.PHONY: help setup up down seed data etl demo console backup restore-test health test security lint check nonprod docs reset
SHELL := /bin/bash
GUARD := .venv/bin/guard
help:         ## show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'
setup:        ## create venv, install guard + dev tools, create .env from template
	python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"
	@[ -f .env ] || (cp .env.example .env && echo "Created .env: EDIT THE PASSWORDS")
up:           ## start PostgreSQL, console, pgAdmin, Prometheus, Grafana (docker)
	docker compose up -d --build
down:         ## stop the stack (keeps data)
	docker compose down
seed:         ## generate + load dimension data (advertisers, campaigns, placements)
	$(GUARD) demo-data dimensions && ./scripts/seed_dimensions.sh
data:         ## generate 30 days of messy ad-network files into data/inbox
	$(GUARD) demo-data backfill --days 30
etl:          ## load everything in data/inbox
	$(GUARD) load
demo:         ## seed + generate + load in one go (database must be up)
	$(MAKE) seed data etl
console:      ## start the web console on http://127.0.0.1:8080
	$(GUARD) console
backup:       ## encrypted backup
	$(GUARD) backup
restore-test: ## restore newest backup into a temp DB and verify
	$(GUARD) restore-test
health:       ## run the health check
	$(GUARD) health
nonprod:      ## masked copy of prod for developers
	$(GUARD) mask-copy
test:         ## unit + console tests
	.venv/bin/python -m pytest -q
security:     ## verify roles/permissions/audit trigger against the live DB
	./tests/test_security.sh
lint:         ## shellcheck all shell scripts
	shellcheck -S warning scripts/*.sh tests/*.sh db/init/*.sh
check:        ## everything CI runs: lint + tests + security (database must be up and loaded)
	$(MAKE) lint test security
docs:         ## build the documentation site into ./site
	.venv/bin/pip install -q mkdocs-material "mkdocs<2" && .venv/bin/mkdocs build
reset:        ## DANGER: delete all containers AND data volumes
	docker compose down -v
