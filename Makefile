.PHONY: up down test-api test-ui triage report clean

up:
	docker compose up -d

down:
	docker compose down -v

test-api:
	pytest tests_api \
		--env=local \
		--alluredir=artifacts/allure-results

test-ui:
	pytest tests_ui \
		--env=local \
		--alluredir=artifacts/allure-results

triage:
	python triage/triage_embed.py
	python triage/triage_cluster.py
	python triage/triage_explain.py
	python triage/triage_gate.py

report:
	allure generate artifacts/allure-results -o reports/allure --clean
	python reports/generate_report.py

clean:
	rm -rf artifacts/*
	rm -rf reports/*
