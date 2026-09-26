PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
.PHONY: verify core historical
verify:
	$(PYTHON) tools/run.py verify
core:
	$(PYTHON) tools/run.py core --output "$(OUTPUT)"
historical:
	$(PYTHON) tools/run.py historical --output "$(OUTPUT)"
