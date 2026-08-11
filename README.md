# FL Studio MCP Controller & Telemetry Bridge

**Repository:** `flstudio-mcp`  
**Location:** `/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp`

Bridge de integración bidireccional entre Agentes IA (vía Model Context Protocol / CoreMIDI) y **FL Studio 21+**.

---

## 🏗️ Arquitectura de Componentes

1. **Hardware Controller Script (`device_Antigravity_MCP.py`)**
   - Instalado en: `~/Documents/Image-Line/FL Studio/Settings/Hardware/AntigravityMCP/`
   - Escucha en tiempo real sobre MIDI Channel 16 / SysEx y mapea llamadas a las APIs de FL Studio (`mixer`, `channels`, `patterns`, `transport`, `general`, `plugins`).

2. **Python MCP Bridge (`scripts/flstudio_mcp_bridge.py`)**
   - Abre un puerto virtual de CoreMIDI en macOS (`Antigravity MCP Out`).
   - Generador de micro-grooves rítmicos (`.mid`) con desfase microtonal y desalineación milimétrica para claps/shakers.
   - Enrutamiento de matrículas de Sidechain automático.
   - Enrutador de Gain/Panorámica y presets de mezcla para stems.

---

## 🚀 Uso Rápido

```bash
# Ejecutar configuración de mezcla y prueba de puerto virtual
python3 scripts/flstudio_mcp_bridge.py
```

### Configuración en FL Studio
1. Abre **FL Studio**.
2. Ve a `Options > MIDI settings`.
3. En la lista de puertos de entrada, selecciona **"Antigravity MCP Out"**.
4. En **Controller type**, selecciona `Antigravity MCP Controller` (o asigna el puerto MIDI `15`).
