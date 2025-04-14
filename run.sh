#!/bin/bash
cd "$(dirname "$0")"
source myenv/bin/activate
python3 -m src.main "$@"
