DUMP_DIR := dumps
DB_USER := tedawards
DB_NAME := tedawards
CONTAINER := tedawards-db-1
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

.PHONY: dump restore

dump:
	mkdir -p $(DUMP_DIR)
	docker exec $(CONTAINER) pg_dump -U $(DB_USER) -Fc $(DB_NAME) > $(DUMP_DIR)/$(DB_NAME)_$(TIMESTAMP).dump
	@echo "Dumped to $(DUMP_DIR)/$(DB_NAME)_$(TIMESTAMP).dump"

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=dumps/tedawards_YYYYMMDD_HHMMSS.dump"; \
		exit 1; \
	fi
	docker exec $(CONTAINER) pg_restore -U $(DB_USER) -d $(DB_NAME) --clean --if-exists /$(FILE)
	@echo "Restored from $(FILE)"
