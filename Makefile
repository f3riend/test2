NAME=secure-box

build:
	uv run python build.py --release

debug:
	uv run python build.py

install:
	uv build
	uv tool install --force dist/secure_box-0.1.0-py3-none-any.whl

check-install:
	secure-box success

remove:
	uv tool uninstall secure-box

upx:
	uv run python build.py --release --upx

test:
	uv run pytest -v

clean:
	uv run python build.py --clean

.PHONY: build debug install check-install remove upx test clean