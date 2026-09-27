all: test

.PHONY: test test-notebooks test-coverage clean

test:
	python -m unittest discover -v -s tests -t .

# execute every notebook under tests/ (needs jupyter: pip install -e ".[dev]"); outputs are not saved
test-notebooks:
	python -m jupyter nbconvert --to notebook --execute --stdout $$(find tests -name "*.ipynb" -not -path "*/.ipynb_checkpoints/*") > /dev/null

test-coverage:
	coverage run -m unittest discover -v -s tests -t .
	coverage report -m

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
