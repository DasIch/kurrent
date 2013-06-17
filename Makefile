help:
	@echo "make help  - Show this message"
	@echo "make dev   - Create development environment"
	@echo "make test  - Run tests"
	@echo "make style - Run pyflakes on all files"
	@echo "make clean - Remove all ignored files and directories"

dev:
	pip install --editable .
	pip install -r dev-requirements.txt

test:
	py.test

style:
	find kurrent tests -iname "*.py" | xargs pyflakes

clean:
	git ls-files --other --directory | xargs rm -r

.PHONY: help dev test style clean
