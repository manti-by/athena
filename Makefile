run:
	uv run uvicorn main:app --host 0.0.0.0 --port 8002 --reload


deploy:
	git pull --ff-only
	uv sync
	sudo systemctl daemon-reload
	sudo systemctl restart athena.service
	sudo service nginx reload

check:
	git add .
	uv run ty check
	uv run pre-commit run

pip:
	uv sync --all-extras --dev

update:
	uv run uv-bump
	uv sync --all-extras --dev
	uv run pre-commit autoupdate

test:
	uv run pytest tests/

migrate:
	uv run alembic upgrade head

migrate-create:
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	uv run alembic downgrade -1

ci: pip check check test
