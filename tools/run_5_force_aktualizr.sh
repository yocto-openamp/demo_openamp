set -euox pipefail

# Force aktualizr-torizon” to check Torizon Cloud for an update immediately.
# On Torizon OS 7.4.0+ the supported way is D-Bus:

sudo busctl call org.uptane.Aktualizr \
  /org/uptane/aktualizr \
  org.uptane.Aktualizr \
  CheckForUpdates

sudo journalctl -f -u aktualizr-torizon
