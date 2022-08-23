export PROTO_PATH=.

fmt:
	poetry run isort .
	poetry run black .
	poetry run mypy . --show-error-codes

gen:
	poetry run protoc -I $$PROTO_PATH --python_out=$$PROTO_PATH --mypy_out=$$PROTO_PATH --proto_path=$$PROTO_PATH $$PROTO_PATH/example/*.proto
	poetry run isort ./example
	poetry run black ./example

test:
	poetry run pytest tests/

clean:
	rm -rf dist

.PHONY: dist
dist:
	poetry build

sdist:
	poetry build -f sdist

publish: clean dist
	poetry publish

release: clean sdist
	ghr -u crflynn -r pbspark -c $(shell git rev-parse HEAD) -delete -b "release" -n $(shell poetry version -s) $(shell poetry version -s) dist/*.tar.gz

setup:
	asdf plugin add python || true
	asdf plugin add poetry || true
	asdf plugin add protoc || true
	asdf plugin add java || true
	asdf install
	poetry install
