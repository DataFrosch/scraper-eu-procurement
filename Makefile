DUMP_DIR := dumps
DB_USER := tedawards
DB_NAME := tedawards
DB_HOST := localhost
DB_PORT := 5432
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

.PHONY: dump restore

dump:
	mkdir -p $(DUMP_DIR)
	PGPASSWORD=$(DB_USER) pg_dump -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -Fc $(DB_NAME) > $(DUMP_DIR)/$(DB_NAME)_$(TIMESTAMP).dump
	@echo "Dumped to $(DUMP_DIR)/$(DB_NAME)_$(TIMESTAMP).dump"

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=dumps/tedawards_YYYYMMDD_HHMMSS.dump"; \
		exit 1; \
	fi
	PGPASSWORD=$(DB_USER) pg_restore -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) --clean --if-exists $(FILE)
	@echo "Restored from $(FILE)"
