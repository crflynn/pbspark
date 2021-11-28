export PROTO_PATH=.

fmt:
	poetry run isort .
	poetry run black .
	poetry run mypy .

gen:
	poetry run protoc -I $$PROTO_PATH --python_out=$$PROTO_PATH --mypy_out=$$PROTO_PATH --proto_path=$$PROTO_PATH $$PROTO_PATH/example/*.proto
	poetry run isort ./example
	poetry run black ./example

test:
	poetry run pytest tests/