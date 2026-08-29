.PHONY: install lint test sign publish clean

install:
	python -m pip install -e ".[dev]"

lint:
	flake8 crownspire tests

test:
	pytest

sign:
	python -m crownspire sign build/manifest.json

publish: sign
	./deploy.sh prod

clean:
	rm -rf build/*.sig __pycache__ .pytest_cache
	find . -name '*.pyc' -delete
