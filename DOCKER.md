# Docker Setup for SDRIG SDK

## Quick Start

### Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- `.env` file with network configuration (see `.env.example`)

### Build and Run

```bash
# Build the Docker image
make build

# Run interactive shell
make shell

# Or using docker-compose
docker-compose run --rm sdrig-sdk
```

## Usage Methods

### Method 1: Using Makefile (Recommended)

```bash
# Show all available commands
make help

# Build image
make build

# Run interactive shell
make shell

# Run examples
make example01  # Device discovery
make example02  # UIO control
make example05  # CAN communication

# Run tests
make test       # All tests
make test-unit  # Unit tests only
```

### Method 2: Using Docker Directly

```bash
# Build
docker build -t sdrig-sdk:latest .

# Run interactive shell
docker run --rm -it \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --env-file .env \
  -v "$PWD":/app \
  sdrig-sdk:latest /bin/bash

# Run specific example
docker run --rm -it \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --env-file .env \
  sdrig-sdk:latest \
  python examples/01_device_discovery.py
```

### Method 3: Using Docker Compose

```bash
# Build
docker-compose build

# Run shell
docker-compose run --rm sdrig-sdk

# Run examples
docker-compose run --rm sdrig-examples

# Run tests
docker-compose run --rm sdrig-tests

# Development mode (persistent container)
docker-compose up -d sdrig-sdk
docker-compose exec sdrig-sdk bash
docker-compose down
```

## Required Capabilities

The container needs special capabilities for AVTP/raw ethernet access:

- `--network host` - Direct access to host network interfaces
- `--cap-add NET_ADMIN` - Network administration privileges
- `--cap-add NET_RAW` - Raw socket access for AVTP

## Environment Variables

Create `.env` file with your network configuration:

```bash
# Network interface
IFACE=enp0s31f6

# AVTP Stream ID
STREAM_ID=1

# Device MAC addresses (optional)
UIO_MAC=66:6A:DB:B3:06:27
ELOAD_MAC=...
IFMUX_MAC=66:6A:DB:B3:06:27

# Logging level
LOG_LEVEL=INFO
```

## Volume Mounts

### Development Mode
Mount the entire project for live code updates:
```bash
-v "$PWD":/app
```

### Examples Only
Mount only examples (read-only):
```bash
-v "$PWD/examples":/app/examples:ro
```

### Tests Only
```bash
-v "$PWD/tests":/app/tests:ro
```

## Image Architecture

### Multi-stage Build
The Dockerfile uses a multi-stage build for optimization:

1. **Builder stage**: Installs build dependencies and Python packages
2. **Runtime stage**: Copies only necessary files, smaller final image

### Image Size
- Builder stage: ~800 MB
- Runtime stage: ~400 MB
- Optimized with `.dockerignore`

### Security
- Runs as non-root user `sdrig`
- Minimal runtime dependencies
- No unnecessary packages

## Troubleshooting

### Permission Denied on Network Interface
```bash
# Run with sudo or add user to required groups
sudo docker run ...
```

### Module Not Found Errors
```bash
# Rebuild image
make clean build
```

### Cannot Access Hardware
```bash
# Check .env file
cat .env

# Verify network interface exists
ip link show

# Check container has proper capabilities
docker run --rm sdrig-sdk:latest ip link show
```

### Python Package Not Found
```bash
# Rebuild with clean cache
docker build --no-cache -t sdrig-sdk:latest .
```

## Development Workflow

### 1. Initial Setup
```bash
make build
```

### 2. Development Loop
```bash
# Start development container
make run

# Inside container:
python examples/01_device_discovery.py

# Exit and rebuild if needed
exit
make build
```

### 3. Testing
```bash
# Unit tests (no hardware required)
make test-unit

# Integration tests (requires hardware)
make test-int
```

### 4. Code Quality
```bash
# Format code
make format

# Lint
make lint

# Type check
make type-check

# All checks
make dev-check
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t sdrig-sdk:test .
      - name: Run tests
        run: docker run --rm sdrig-sdk:test pytest tests/unit/ -v
```

### GitLab CI Example
```yaml
docker-build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker run --rm $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA pytest tests/unit/ -v
```

## Cleanup

```bash
# Remove containers and image
make clean

# Remove everything including volumes
make clean-all

# Docker system cleanup
docker system prune -af
```

## Advanced Usage

### Custom Network Interface
```bash
docker run --rm -it \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  -e IFACE=eth0 \
  sdrig-sdk:latest /bin/bash
```

### Debug Mode
```bash
docker run --rm -it \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  --env-file .env \
  -e LOG_LEVEL=DEBUG \
  sdrig-sdk:latest \
  python examples/01_device_discovery.py
```

### Packet Capture
```bash
# Inside container
tcpdump -i enp0s31f6 -w /tmp/capture.pcap ether proto 0x22f0
```

## Best Practices

1. **Always use `.env` file** for configuration
2. **Mount volumes read-only** when possible
3. **Use make targets** for consistency
4. **Clean up regularly** to save disk space
5. **Test in container** before deploying
6. **Use multi-stage build** for smaller images
7. **Pin dependency versions** in requirements.txt

## Support

For issues and questions:
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Documentation: https://github.com/soda-auto/soda-validate-sdrig-sdk-py
