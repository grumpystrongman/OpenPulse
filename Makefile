.PHONY: init seed test rebuild reset openapi

init:
	powershell -ExecutionPolicy Bypass -File scripts/init.ps1

seed:
	powershell -ExecutionPolicy Bypass -File scripts/seed.ps1

test:
	powershell -ExecutionPolicy Bypass -File scripts/test.ps1

rebuild:
	powershell -ExecutionPolicy Bypass -File scripts/rebuild.ps1

reset:
	powershell -ExecutionPolicy Bypass -File scripts/reset.ps1

openapi:
	python scripts/export_openapi.py
