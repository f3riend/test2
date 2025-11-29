NAME=secure-box

build:
	uv run python build.py --release

debug:
	uv run python build.py

upx:
	uv run python build.py --release --upx

clean:
	uv run python build.py --clean
