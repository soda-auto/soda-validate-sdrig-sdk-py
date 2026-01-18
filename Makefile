.PHONY: help build run shell test clean examples

# Docker image name
IMAGE_NAME = sdrig-sdk:latest

# Default target
help:
	@echo "SDRIG SDK - Docker Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Build & Run:"
	@echo "  make build       - Build Docker image"
	@echo "  make shell       - Run interactive shell"
	@echo "  make run         - Run with docker-compose"
	@echo ""
	@echo "Examples:"
	@echo "  make example01   - Run device discovery example"
	@echo "  make example02   - Run UIO control example"
	@echo "  make example03   - Run ELoad control example"
	@echo "  make example04   - Run IfMux control example"
	@echo "  make example05   - Run CAN communication example"
	@echo "  make example06   - Run LIN communication example"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run unit tests"
	@echo "  make test-unit   - Run only unit tests"
	@echo "  make test-int    - Run integration tests (requires hardware)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove Docker containers and images"
	@echo "  make clean-all   - Remove everything including volumes"
	@echo ""

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .

# Run interactive shell
shell:
	@echo "Starting interactive shell..."
	docker run --rm -it \
		--network host \
		--cap-add NET_ADMIN \
		--cap-add NET_RAW \
		--env-file .env \
		-v "$$PWD":/app \
		$(IMAGE_NAME) /bin/bash

# Run with docker-compose
run:
	docker-compose up -d sdrig-sdk
	docker-compose exec sdrig-sdk bash

# Stop docker-compose services
stop:
	docker-compose down

# Run examples
example01:
	@echo "Running Example 01: Device Discovery"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/01_device_discovery.py

example02:
	@echo "Running Example 02: UIO Control"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/02_uio_control.py

example03:
	@echo "Running Example 03: ELoad Control"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/03_eload_control.py

example04:
	@echo "Running Example 04: IfMux Control"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/04_ifmux_control.py

example05:
	@echo "Running Example 05: CAN Communication"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/05_can_communication.py

example06:
	@echo "Running Example 06: LIN Communication"
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) python examples/06_lin_communication.py

# Run tests
test:
	@echo "Running all tests..."
	docker run --rm $(IMAGE_NAME) pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	docker run --rm $(IMAGE_NAME) pytest tests/unit/ -v

test-int:
	@echo "Running integration tests (requires hardware)..."
	docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
		--env-file .env $(IMAGE_NAME) pytest tests/test_integration_all_messages.py -v

# Cleanup
clean:
	@echo "Cleaning up Docker containers and images..."
	docker-compose down
	docker rmi $(IMAGE_NAME) || true

clean-all: clean
	@echo "Removing all Docker data..."
	docker system prune -af --volumes

# Development commands
install-deps:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

format:
	black sdrig/ tests/ examples/

lint:
	pylint sdrig/

type-check:
	mypy sdrig/

dev-check: format lint type-check test-unit
	@echo "✅ All development checks passed!"
