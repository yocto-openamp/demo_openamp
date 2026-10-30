set -x

REPO_DIR=$(dirname "$PWD")
if [[ ! -f $REPO_DIR/PROJECT_MARKER.txt ]]; then
	echo "ERROR: Start this script from the corresponding folder!" >&2
	exit 1
fi

$REPO_DIR/app_emw/.venv/bin/python -m app_emw.app.main_dump_imu_measurements
