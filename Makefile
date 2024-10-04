all: test

.PHONY: test

test:
	python -m unittest discover -v -s tests -t .

test-coverage:
	coverage run -m unittest discover -v -s tests -t .
	coverage report -m

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
