init:
	if [ ! -d "venv" ]; then python3 -m venv venv; fi
	python3 -m pip install --upgrade pip
	pip install -r requirements.txt

active:
	. venv/bin/activate
	python3 -m pip install --upgrade pip

test:
	py.test tests

.PHONY: init test active
