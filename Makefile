PYTHON ?= python3
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
.PHONY: verify core historical figures documents
verify:
	$(PYTHON) tools/run.py verify
core:
	$(PYTHON) tools/run.py core $(if $(strip $(OUTPUT)),--output "$(OUTPUT)",)
historical:
	$(PYTHON) tools/run.py historical $(if $(strip $(OUTPUT)),--output "$(OUTPUT)",)
figures:
	$(PYTHON) tools/build_figures.py --output "$(if $(strip $(OUTPUT)),$(OUTPUT),.build/figures-1)"
documents:
	$(PYTHON) tools/build_documents.py --output "$(if $(strip $(OUTPUT)),$(OUTPUT),.build/documents-1)"
