
.PHONY: clean-pyc clean-build


clean-pyc:
	find . -name '*.pyc' -exec rm {} +
	find . -name '*.pyo' -exec rm {} +
	find . -name '*~' -exec rm {} +


tests: clean-pyc
	AWS_PROFILE=jensfinnas PYTHONPATH=. py.test tests --verbose

test: clean-pyc
	AWS_PROFILE=jensfinnas PYTHONPATH=. py.test $(file) --verbose

serve:
	sls wsgi serve --stage local

deploy:
	sls deploy --aws-profile jensfinnas

logs:
	sls logs -f app --aws-profile jensfinnas
