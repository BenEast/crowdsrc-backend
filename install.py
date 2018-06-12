from subprocess import call
import sys

UPGRADE = False

# Get upgrade flag
if '-u' in sys.argv or '--upgrade' in sys.argv:
    UPGRADE = True

# This script installs the dependencies listed in the 'dependencies' file
with open('dependencies', 'r') as f:
    for dependency in f:
        dependency = dependency.strip()

        if not dependency:
            continue

        if UPGRADE:
            call('pip install --upgrade ' + dependency)
        else:
            call('pip install ' + dependency)
