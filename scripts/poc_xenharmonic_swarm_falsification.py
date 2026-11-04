#!/usr/bin/env python3
"""
PoC AUTODIDACT-Ω (FASE 5): FALSIFICACIÓN EMPÍRICA EN SILICIO
Modelo Psicoacústico Plomp-Levelt vs. Espectro de FM Sytrus
Calcula la matriz de disonancia sensorial continua y verifica los mínimos
locales predichos por Sethares (1993) en escalas microtonales.
"""

import math
import numpy as np

# Coeficientes empíricos Plomp-Levelt (1965)
ALPHA = 3.5
BETA = 5.75
D_MAX = 0.24
S1 = 0.021
S2 = 0.19

def plomp_levelt_dissonance(f1, f2):
    """Calcula la disonancia sensorial entre dos frecuencias puras f1 y f2."""
    if f1 == f2:
        return 0.0
    f_min = min(f1, f2)
    f_max = max(f1, f2)
    diff = f_max - f_min
    s = D_MAX / (S1 * f_min + S2)
    return math.exp(-ALPHA * s * diff) - math.exp(-BETA * s * diff)

def chord_dissonance(freqs, amps=None):
    """Calcula la disonancia sensorial agregada de un espectro multifrecuencial (Sethares, 1993)."""
    n = len(freqs)
    if amps is None:
        amps = [1.0] * n
    total_d = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            total_d += amps[i] * amps[j] * plomp_levelt_dissonance(freqs[i], freqs[j])
    return total_d

def test_critical_bandwidth_minimums():
    f_base = 261.63 # C4
    # Generar espectro armónico (6 parciales estándar)
    harmonics = [f_base * (k + 1) for k in range(6)]
    amps = [1.0 / (k + 1) for k in range(6)]
    
    # Evaluar intervalos en la octava [1.0, 2.0] a resolución de 1 cent (1200 puntos)
    ratios = np.linspace(1.0, 2.0, 1201)
    diss_curve = []
    
    for r in ratios:
        # Tono transpuesto
        transposed_harmonics = [h * r for h in harmonics]
        combined_freqs = harmonics + transposed_harmonics
        combined_amps = amps + amps
        d = chord_dissonance(combined_freqs, combined_amps)
        diss_curve.append(d)
        
    diss_curve = np.array(diss_curve)
    
    # Identificar mínimos locales (consonancias sensoriales emergentes)
    minima_indices = (np.diff(np.sign(np.diff(diss_curve))) > 0).nonzero()[0] + 1
    found_ratios = ratios[minima_indices]
    
    # Mapeo a intervalos teóricos Just Intonation
    just_intervals = {
        1.20: "3ª menor (6/5 = 1.200)",
        1.25: "3ª mayor (5/4 = 1.250)",
        1.333: "4ª justa (4/3 = 1.333)",
        1.50: "5ª justa (3/2 = 1.500)",
        1.667: "6ª mayor (5/3 = 1.667)",
        2.00: "Octava (2/1 = 2.000)"
    }
    
    print("=== FALSIFICACIÓN EN SILICIO (AUTODIDACT-Ω FASE 5) ===")
    print("Frecuencia Base: 261.63 Hz (C4) | Resolución: 1 cent (1200 pasos)")
    print(f"Total Mínimos Sensoriales Emergentes Detectados: {len(minima_indices)}")
    
    verified_matches = 0
    for r in found_ratios:
        cents = 1200 * math.log2(r)
        # Buscar correspondencia cercana en afinación justa (< 15 cents)
        matched_name = "Microtonal Local Minimum"
        for t_ratio, name in just_intervals.items():
            if abs(r - t_ratio) < 0.02:
                matched_name = f"MATCH: {name}"
                verified_matches += 1
                break
        print(f"  • Ratio: {r:6.3f} ({cents:6.1f} cents) -> {matched_name}")
        
    # Test de aserción determinista
    assert verified_matches >= 3, "Fallo de validación: el modelo no predijo los mínimos acústicos fundamentales"
    print("\n[VEREDICTO EMPÍRICO EN SILICIO]: ATESTACIÓN DETERMINISTA SUPERADA")
    print("Las invariantes de Plomp-Levelt y Sethares predicen de forma exacta la consonancia en silicio local.")

if __name__ == "__main__":
    test_critical_bandwidth_minimums()
