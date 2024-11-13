NODE_VERSION := 22.8.0
MIN_NODE_VERSION := 16.20.2

# Detect the shell (sh, bash, etc.)
SHELL := $(shell echo $$SHELL)

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help install update run

help:
	@echo "--------------- HELP ---------------"
	@echo "To install frontend dependencies: make install"
	@echo "To update frontend dependencies: make update"
	@echo "To start the frontend server: make run"
	@echo "------------------------------------"

install:
	@npm install

update:
	@npm update

run:
	@echo "🚀 Starting frontend development server..."
	@export NVM_DIR="$$HOME/.nvm"; \
	if [ -s "$$NVM_DIR/nvm.sh" ]; then \
		. "$$NVM_DIR/nvm.sh"; \
		INSTALLED_VERSIONS=$$(nvm ls --no-colors --no-alias | grep -o 'v[0-9.]\+' | sed 's/v//g'); \
		if echo "$$INSTALLED_VERSIONS" | grep -q "^$(NODE_VERSION)"; then \
			TARGET_VERSION="$(NODE_VERSION)"; \
			echo "✅ Using Node.js version $(NODE_VERSION)"; \
		else \
			VERSIONS_ABOVE_MIN=$$(echo "$$INSTALLED_VERSIONS" | awk -v min="$(MIN_NODE_VERSION)" '{split($$1,a,"."); if(a[1]>=min) print $$1}' | sort -n); \
			if [ -n "$$VERSIONS_ABOVE_MIN" ]; then \
				TARGET_VERSION=$$(echo "$$VERSIONS_ABOVE_MIN" | tail -n1); \
				echo "⚠️ Node.js $(NODE_VERSION) not found, using version $$TARGET_VERSION instead"; \
			else \
				echo "⚠️ No compatible Node.js version found (min: $(MIN_NODE_VERSION)). Installing..."; \
				nvm install $(NODE_VERSION); \
				TARGET_VERSION="$(NODE_VERSION)"; \
				echo "✅ Installed Node.js version $(NODE_VERSION)"; \
			fi; \
		fi; \
		if [ -n "$$TARGET_VERSION" ]; then \
			nvm use "$$TARGET_VERSION" && npm run dev; \
		else \
			npm run dev; \
		fi; \
	else \
		echo "⚠️ nvm not found, using system Node.js"; \
		npm run dev; \
	fi