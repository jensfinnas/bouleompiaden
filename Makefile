
.PHONY: clean-pyc clean-build

install:
	virtualenv env
	. env/bin/activate
	pip install -r requirements.txt
	cp .env.sample .env

clean-pyc:
	find . -name '*.pyc' -exec rm {} +
	find . -name '*.pyo' -exec rm {} +
	find . -name '*~' -exec rm {} +


tests: clean-pyc
	AWS_PROFILE=jensfinnas PYTHONPATH=. py.test tests --verbose

test: clean-pyc
	AWS_PROFILE=jensfinnas PYTHONPATH=. py.test $(file) --verbose

serve:
	sls wsgi serve

deploy:
	sls deploy --aws-profile jensfinnas
