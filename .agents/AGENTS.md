## Reglas Específicas del Workspace (C5-REAL / SMT Verification)

- **Invariante de Verificación Formal SMT y Cero Existence-Gaps C5-REAL.** Antes de declarar completada cualquier modificación o refactorización de código en el workspace, el agente DEBE:
  1. Auditar que todos los símbolos importados, módulos y primitivas existan físicamente en el sistema de archivos (sin alucinaciones ni dependencias fantasma).
  2. Validar los contratos lógicos y la coherencia del estado mediante las puertas de verificación determinista disponibles (como `fast_smt_gate.py` o verificadores de invariantes).
  3. Rehusar parches superficiales que oculten errores o silencien excepciones sin solucionar la causa raíz del invariante violado.

- **Orquestación Resiliente de Enjambres Kimi K3 y Fallback Multi-Backend.** Al delegar análisis o tareas masivas vía Kimi K3 (`kimi-nexus`), el agente DEBE:
  1. **Filtrado de Exergía**: No delegar tareas triviales que el agente local pueda resolver deterministamente sin consumo adicional de red.
  2. **Control de Thrashing**: Supervisar la telemetría de kernel (`ru_nivcsw`). Si el cambio inútil de contexto supera 2132, reducir la topología de núcleos/hilos ($P \times S$).
  3. **Conmutación Soberana por Fallo**: Si la API remota de Moonshot devuelve errores 429/500 o fallos de red, conmutar inmediatamente al backend local `local_vllm` (`localhost:8000`) o `local_mlx`.
  4. **Reducción de Anergía**: Canalizar los outputs paralelos del enjambre a través de `AnergyReducer` antes de presentar el artefacto sintético final.

