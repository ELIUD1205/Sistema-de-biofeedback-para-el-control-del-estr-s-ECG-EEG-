# Sistema de biofeedback para el control del estrés (ECG + EEG) 
Este repositorio contiene el desarrollo de una interfaz gráfica para un sistema biofeedback automatizado y procesamiento digital de señales biomédicas en tiempo real. La aplicación está diseñada para cargar, analizar y visualizar registros biopotenciales adquiridos a través del sistema **BIOPAC MP36**, enfocándose en la detección bimodal de estados de estrés o relajación mediante el monitoreo simultáneo de señales neuronales y cardíacas.

## Configuración de Adquisición (Biopac MP36)
**Canal 1 (Índice 0): EEG Interhemisférico**
  * **Posicionamiento:** Electrodos colocados para medir la diferencia de potencial interhemisférica (en posiciones centrales partiendo de Cz).
  * **Objetivo:** Obtener la fluctuación de energia de la **Onda Alfa (8-13 Hz)** para determinar el estado de reposo cognitivo.
**Canal 2 (Índice 1): ECG (Derivación II)**
  * **Posicionamiento:** Configuración estándar de Einthoven (Brazo derecho [-], Pierna izquierda [+], Pierna derecha [Tierra]).
  * **Objetivo:** Extracción de picos R para el cálculo evolutivo de la Variabilidad de la Frecuencia Cardíaca (HRV) en los dominios del tiempo (**RMSSD**) y de la frecuencia (**Relación LF/HF**).
