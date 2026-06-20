# Funcionamiento Interno del Código: Biofeedback Embebido
Este documento detalla la arquitectura de software, los modelos matemáticos y el flujo de ejecución por bloques del script de procesamiento bimodal en tiempo real.

## Arquitectura General del Flujo
El programa opera bajo un modelo de **concurrencia basada en eventos** mediante el método `.after()` de Tkinter. Esto evita el congelamiento de la interfaz gráfica (GUI) al separar la actualización visual del procesamiento de señales pesadas.

[Archivo .acq] ──> [bioread] ──> [Señal EEG / Señal ECG]
│
┌──────────────────────────┴──────────────────────────┐

▼                                                     ▼

[Ventana Deslizante 2s]                               [Ventana Deslizante 2s]
│                                                     │
[Filtro Paso Banda 8-13 Hz]                           [Filtro Paso Banda 5-15 Hz]
│                                                     │
[FFT / Espectro PSD]                                  [find_peaks (Picos R)]
│                                                     │
▼                                                     ▼

(Potencia Banda Alfa)                                   (BPM, RMSSD, LF/HF)

│                                                     │
└──────────────────────────┬──────────────────────────┘
▼
[Lógica del Semáforo Bimodal]
│
┌────────────────┴────────────────┐
▼                                 ▼
🟢 RELAJACIÓN (CALMA)              🔴 ALERTA / ESTRÉS

## 1. Procesamiento de la Señal EEG (Canal 1)

El objetivo en este canal es cuantificar la actividad síncrona en la corteza cerebral en estado de reposo a través de la **Banda Alfa**.

### A. Filtrado Digital (Paso Banda)
Para aislar las frecuencias de interés (8 a 13 Hz) y eliminar el ruido de alta frecuencia o artefactos de movimiento, se emplea un filtro **Butterworth de 4° orden** implementado mediante `scipy.signal.filtfilt`:
* **`filtfilt` (Fase Cero):** Aplica el filtro hacia adelante y hacia atrás sobre el vector de datos. Esto corrige cualquier desfase temporal inducido por el filtro, manteniendo alineados los eventos biológicos con el tiempo real de visualización.

### B. Análisis del Dominio de la Frecuencia (FFT y PSD)
Una vez limpia la señal, la función `calcular_potencia_alfa()` ejecuta:
1. **`np.fft.rfft`:** Transformada Rápida de Fourier para señales reales, convirtiendo el bloque de 2 segundos del dominio del tiempo al de la frecuencia.
2. **Cálculo de la PSD (Densidad Espectral de Potencia):** $$\text{PSD} = \frac{1}{N} \cdot |X(f)|^2$$
3. **Integración:** Se suman los valores de la PSD correspondientes únicamente a los índices de frecuencia entre $8.0$ y $13.0\text{ Hz}$. Un valor alto representa un cerebro en calma y libre de carga cognitiva pesada.

## 2. Procesamiento de la Señal ECG y HRV (Canal 2)

El análisis cardíaco se centra en la extracción del complejo QRS y el estudio micro-estructural de la Variabilidad de la Frecuencia Cardíaca (HRV).

### A. Detección de Picos R
1. La señal se filtra entre **5 y 15 Hz** con un filtro Butterworth de fase cero de 3er orden. Este rango elimina la interferencia de la línea eléctrica ($60\text{ Hz}$) y las fluctuaciones respiratorias de baja frecuencia, resaltando la onda R del ECG.
2. La función `find_peaks` localiza los máximos locales utilizando dos umbrales adaptativos:
   * **`height`:** Debe superar el 50% de la amplitud máxima detectada en la ventana activa para evitar falsos positivos con ondas T prominentes.
   * **`distance`:** Distancia mínima correspondiente a un periodo de refracción fisiológico ($0.4 \cdot f_s = 400\text{ ms}$), limitando el cálculo a un máximo teórico de 150 BPM.

### B. Extracción de Métricas de HRV
A partir del vector de diferencias temporales entre picos sucesivos ($\text{Intervalos R-R}$ en segundos), se calculan tres variables críticas:
* **Frecuencia Cardíaca (BPM):** Media aritmética de los latidos extrapolada a un minuto.
* **RMSSD (Dominio del Tiempo):** Raíz cuadrada de la media de las diferencias al cuadrado de intervalos R-R sucesivos. Mide directamente la actividad del nervio vago (sistema parasimpático).
* **Relación LF/HF (Dominio de la Frecuencia/Estimación):** Relación de desviación estándar entre las diferencias de intervalos sucesivos y los intervalos directos. Se utiliza como indicador del **Balance Simpático-Vagal**.
