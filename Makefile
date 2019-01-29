configure:
	pipenv install --dev

test:
	pipenv run pytest --cov-config .coveragerc --cov-report xml --cov=. .

lint:
	pipenv run pylint transformer/*.py > pylint-report.txt || true

