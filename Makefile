help:
	@echo "make help          - Show this message"
	@echo "make dev           - Create development environment"
	@echo "make test          - Run tests"
	@echo "make style         - Run pyflakes on all files"
	@echo "make coverage      - Make coverage report"
	@echo "make view-coverage - View coverage report in a browser"
	@echo "make clean         - Remove all ignored files and directories"

dev:
	pip install --editable .
	pip install -r dev-requirements.txt

test:
	py.test -r s

style:
	find kurrent tests -iname "*.py" | xargs pyflakes

coverage:
	py.test --cov kurrent

view-coverage: coverage
	coverage html
	open htmlcov/index.html

clean:
	git ls-files --other --directory | xargs rm -r

.PHONY: help dev test style coverage view-coverage clean
