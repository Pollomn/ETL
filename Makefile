# Makefile for Dropshipping Pipeline (using uv + ruff)
PYTHON ?= python3
UV ?= uv

.PHONY: help install jupyter lint fmt test clean generate-data docker-up docker-down validate monitor all

help:
	@echo "Dropshipping Pipeline Commands:"
	@echo " make install - Install dependencies with uv"
	@echo " make generate-data - Generate seed data (customers, inventory, orders)"
	@echo " make docker-up - Start Redpanda (Kafka) with Docker Compose"
	@echo " make docker-down - Stop Docker containers"
	@echo " make validate - Run data validation checks"
	@echo " make monitor - Start Streamlit dashboard"
	@echo " make all - Run complete pipeline setup"
	@echo ""
	@echo "Development commands:"
	@echo " make jupyter - Launch Jupyter Notebook"
	@echo " make lint - Run ruff linter"
	@echo " make fmt - Auto-format with ruff"
	@echo " make test - Run pytest"
	@echo " make clean - Remove caches and artifacts"

install: 
	$(UV) sync

generate-data:
	@echo "🚀 Generating seed data..."
	python3 scripts/export_seed.py --customers 1000 --products 200 --orders 5000 --seed 42

docker-up:
	@echo "🐳 Starting Redpanda (Kafka)..."
	cd docker && docker-compose up -d
	@echo "✅ Redpanda started. Kafka available at localhost:9092"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	cd docker && docker-compose down
	@echo "✅ Containers stopped"

validate:
	@echo "🔍 Running validation checks..."
	$(UV) run python scripts/validate.py

monitor:
	@echo "📊 Starting Streamlit dashboard..."
	$(UV) run streamlit run streamlit_monitor/app.py

all: install generate-data docker-up
	@echo "🎉 Pipeline setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure .env with your Snowflake credentials"
	@echo "2. Run: bash snowflake/run_all.sh"
	@echo "3. Start producer: $(UV) run python scripts/producer.py --mode replay --rate 10"
	@echo "4. Start consumer: $(UV) run python scripts/consumer_snowflake.py"
	@echo "5. Run validation: make validate"
	@echo "6. Start monitoring: make monitor"

jupyter: 
	$(UV) run jupyter notebook

lint: 
	$(UV) run ruff check .

fmt: 
	$(UV) run ruff format .

test: 
	$(UV) run pytest -q

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .ipynb_checkpoints
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name 'dist' -exec rm -rf {} +
	rm -rf data/seed/*.csv reports/*.json
