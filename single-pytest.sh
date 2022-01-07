#!/bin/bash
pytest $1 --cov-report= --cov
coveragepy-lcov --data_file_path .coverage --output_file_path lcov.info
sed -i 's/\/klub-v/\/home\/timothy\/pu\/auto-mat\/klub/g' lcov.info
