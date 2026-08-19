set -euox pipefail

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

cd $REPO_DIR

uv venv --python 3.13.13
. .venv/bin/activate
uv pip install -e .[dev]

