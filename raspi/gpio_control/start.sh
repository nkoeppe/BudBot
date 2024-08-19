#!/bin/bash
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- python -m app.main