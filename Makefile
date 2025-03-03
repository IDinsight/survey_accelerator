include ./deployment/docker-compose/.backend.env

PROJECT_NAME=hew-ai
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
ENDPOINT_URL = localhost:8000

guard-%:
	@if [ -z '${${*}}' ]; then echo 'ERROR: environment variable $* not set' && exit 1; fi


setup-db: guard-POSTGRES_USER guard-POSTGRES_PASSWORD guard-POSTGRES_DB
	-@docker stop survey-accelerator
	-@docker rm survey-accelerator
	@docker system prune -f
	@sleep 2
	@docker run --name survey-accelerator \
		-e POSTGRES_USER=${POSTGRES_USER} \
		-e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
		-e POSTGRES_DB=${POSTGRES_DB} \
		-p ${POSTGRES_PORT}:5432 \
		-d pgvector/pgvector:pg16
	@sleep 5
	set -a && \
        source "$(CURDIR)/deployment/docker-compose/.backend.env" && \
        set +a && \
	cd backend && \
	python -m alembic upgrade head

teardown-db:
	@docker stop survey-accelerator
	@docker rm survey-accelerator
