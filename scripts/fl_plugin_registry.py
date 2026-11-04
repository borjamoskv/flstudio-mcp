#!/usr/bin/env python3
"""
Antigravity FL Studio Native & VST Plugin Registry Engine (RAE SOTA)
Contains complete scanned plugin inventory, RAE definitions, mathematical DSP transfer functions,
MIDI CC parameter mappings, and binary .fst structures for all 51 Native Generators,
89 Native Effects, and 7 VST3/AU Plugins (147 plugins total).
"""

from typing import Any, Dict

from scripts.fl_native_plugin_reverse_engine import (
    EFFECTS_RAE_SPEC,
    FL_CORE_ARCHITECTURE_RAE,
    FL_EVENT_CODES,
    GENERATORS_RAE_SPEC,
    RAE_ACOUSTIC_LEXICON,
    VST3_PLUGINS_RAE_SPEC,
    inspect_plugin_rae,
    scan_native_fl_plugins,
    search_rae_lexicon,
)

NATIVE_GENERATORS: Dict[str, Dict[str, Any]] = GENERATORS_RAE_SPEC
NATIVE_EFFECTS: Dict[str, Dict[str, Any]] = EFFECTS_RAE_SPEC
THIRD_PARTY_PLUGINS: Dict[str, Dict[str, Any]] = VST3_PLUGINS_RAE_SPEC


def get_plugin_inventory_summary() -> Dict[str, Any]:
    return {
        "native_generators_count": len(NATIVE_GENERATORS),
        "native_effects_count": len(NATIVE_EFFECTS),
        "third_party_vst3_count": len(THIRD_PARTY_PLUGINS),
        "total_plugins_count": len(NATIVE_GENERATORS) + len(NATIVE_EFFECTS) + len(THIRD_PARTY_PLUGINS),
        "core_subsystems_count": len(FL_CORE_ARCHITECTURE_RAE),
        "binary_event_codes_count": len(FL_EVENT_CODES),
        "rae_lexicon_terms_count": len(RAE_ACOUSTIC_LEXICON),
        "generators": list(NATIVE_GENERATORS.keys()),
        "effects": list(NATIVE_EFFECTS.keys()),
        "vst3": list(THIRD_PARTY_PLUGINS.keys()),
    }


__all__ = [
    "NATIVE_GENERATORS",
    "NATIVE_EFFECTS",
    "THIRD_PARTY_PLUGINS",
    "FL_CORE_ARCHITECTURE_RAE",
    "FL_EVENT_CODES",
    "RAE_ACOUSTIC_LEXICON",
    "get_plugin_inventory_summary",
    "inspect_plugin_rae",
    "search_rae_lexicon",
    "scan_native_fl_plugins",
]
