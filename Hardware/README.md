Este apartado documenta los componentes físicos, sistemas de adquisición clínica y las derivaciones de electrodos utilizados para el registro bimodal de biopotenciales.

## 1. BIOPAC MP36
El **BIOPAC MP36** es un sistema de adquisición de datos de grado médico y de investigación diseñado para registrar variables fisiológicas con un alto índice de seguridad y aislamiento eléctrico.
* **Características técnicas:** Cuenta con un convertidor analógico-digital (ADC) de 24 bits, amplificadores de alta ganancia controlados por software y filtros analógicos integrados.
* **Frecuencia de Muestreo ($f_s$):** Configurado a **2000 Hz** (2000 muestras por segundo), garantizando una resolución temporal óptima para evitar el solapamiento de frecuencias (aliasing) en señales de ECG y EEG de acuerdo con el teorema de Nyquist.
* **Conexión:** Los módulos de aislamiento derivan la señal bioeléctrica procesada directamente a la computadora a través de un puerto USB seguro.

![BIOPAC MP36](BIOPAC.jpeg)

## 2. Derivaciones Electroencefalograma (EEG)
Para registrar de la actividad eléctrica cerebral cortical orientada al Biofeedback, se empleó un montaje simplificado basado en el **Sistema Internacional 10-20**.
* **Configuración Bimodal (Canal 1):** Se utilizo la derivación interhemisférica  **Cz (C3 - C4)** referenciadas al pomul derecho como tierra física.
* **Fisiología del Ritmo Alfa:** Esta ubicación sobre la corteza sensitivo-motora y frontal es idónea para medir la sincronización neuronal. Al cerrar los ojos, el cerebro entra en un estado de reposo metabólico, reflejado en un aumento drástico de la amplitud del **Ritmo Alfa (8 - 13 Hz)**. Al abrir los ojos (estímulo visual), ocurre el fenómeno de desincronización o "Bloqueo Alfa", reduciendo la potencia espectral de inmediato.

![Derivacion EEG(Derivaciones EEG.png)

