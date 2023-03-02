BUILD := $(shell git describe --tags --always --dirty)
DIR := $(shell pwd)

# define image names
APP      := duty_csv
REGISTRY := seglh

# build tags
IMG           := $(REGISTRY)/$(APP)
IMG_VERSIONED := $(IMG):$(BUILD)
IMG_LATEST    := $(IMG):latest

.PHONY: push build version cleanbuild

push: build
	docker push $(IMG_VERSIONED)
	docker push $(IMG_LATEST)

build: version
	docker buildx build --platform linux/amd64 -t $(IMG_VERSIONED) . || docker build -t $(IMG_VERSIONED) .
	docker tag $(IMG_VERSIONED) $(IMG_LATEST)
	# docker save $(IMG_VERSIONED) | gzip > $(DIR)/$(IMG_VERSIONED).tar.gz

version:
	echo $(BUILD) > VERSION

cleanbuild:
	docker buildx build --platform linux/amd64 --no-cache -t $(IMG_VERSIONED) .
