include ./backend/.env

PROJECT_NAME=hew-ai
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
ENDPOINT_URL=localhost:8000

# fail if any of these vars is unset or empty
guard-%:
	@if [ -z '${${*}}' ]; then \
	  echo "ERROR: environment variable $* not set"; \
	  exit 1; \
	fi

setup-db: guard-POSTGRES_USER guard-POSTGRES_PASSWORD guard-POSTGRES_DB guard-POSTGRES_PORT
	# stop & remove any old container
	-@docker stop survey-accelerator 2>/dev/null || true
	-@docker rm   survey-accelerator 2>/dev/null || true

	# clean up unused Docker artifacts
	@docker system prune -f
	@sleep 2

	# 1) start Postgres on host:5434 → container:5432
	@docker run --name survey-accelerator \
	  -e POSTGRES_USER=${POSTGRES_USER} \
	  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	  -e POSTGRES_DB=${POSTGRES_DB} \
	  -p ${POSTGRES_PORT}:5432 \
	  -d pgvector/pgvector:pg16
	@sleep 5

	# 2) run Alembic migrations
	@set -a && \
	  source "$(CURDIR)/backend/.env" && \
	  set +a && \
	  cd backend && \
	  python -m alembic upgrade head

teardown-db:
	@docker stop survey-accelerator 2>/dev/null || true
	@docker rm   survey-accelerator 2>/dev/null || true
