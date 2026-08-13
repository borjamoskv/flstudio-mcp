## Reglas Específicas del Workspace (C5-REAL / SMT Verification)

- **Invariante de Verificación Formal SMT y Cero Existence-Gaps C5-REAL.** Antes de declarar completada cualquier modificación o refactorización de código en el workspace, el agente DEBE:
  1. Auditar que todos los símbolos importados, módulos y primitivas existan físicamente en el sistema de archivos (sin alucinaciones ni dependencias fantasma).
  2. Validar los contratos lógicos y la coherencia del estado mediante las puertas de verificación determinista disponibles (como `fast_smt_gate.py` o verificadores de invariantes).
  3. Rehusar parches superficiales que oculten errores o silencien excepciones sin solucionar la causa raíz del invariante violado.
