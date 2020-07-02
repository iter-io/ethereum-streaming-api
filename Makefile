IMAGE := 609256465469.dkr.ecr.us-east-1.amazonaws.com/iter-io/ethereum-etl:$(shell date "+%Y%m%dT%H%m%S")
IMAGE_LATEST := 609256465469.dkr.ecr.us-east-1.amazonaws.com/iter-io/ethereum-etl:latest

auth_docker:
	eval `aws ecr get-login --no-include-email`

build:
	docker build . -t $(IMAGE) -t $(IMAGE_LATEST) -f src/ethereum-streaming-api/Dockerfile .

push: build
	$(MAKE) auth_docker && docker push $(IMAGE)
	$(MAKE) auth_docker && docker push $(IMAGE_LATEST)

run:
    kubectl run 609256465469.dkr.ecr.us-east-1.amazonaws.com/iter-io/ethereum-etl:latest
