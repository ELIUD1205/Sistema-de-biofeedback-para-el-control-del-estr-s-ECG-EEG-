import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from scipy.signal import butter, lfilter, filtfilt
from scipy.signal import find_peaks

# Integración de Matplotlib con Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Intentar importar la librería correcta de BIOPAC
try:
    import bioread
except ImportError:
    messagebox.showerror("Librería faltante", "Por favor instala la librería correcta ejecutando:\npip install bioread")

# ==========================================
# 1. PARÁMETROS CONFIGURABLES
# ==========================================
WINDOW_SEC = 2     # Ventana de procesamiento de 2 segundos
UPDATE_MS = 200    # Simulación de avance de tiempo cada 200 ms (5 Hz)

# ==========================================
# 2. FILTRADO Y PROCESAMIENTO DIGITAL
# ==========================================
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return filtfilt(b, a, data)

def calcular_potencia_alfa(eeg_data, fs):
    """Filtra en la banda Alfa (8-13 Hz) y calcula la PSD mediante FFT"""
    eeg_filtrado = bandpass_filter(eeg_data, 8.0, 13.0, fs, order=4)
    n = len(eeg_filtrado)
    fft_vals = np.fft.rfft(eeg_filtrado)
    fft_freqs = np.fft.rfftfreq(n, 1/fs)
    
    psd = (1.0 / n) * np.abs(fft_vals)**2
    alfa_idx = np.where((fft_freqs >= 8.0) & (fft_freqs <= 13.0))[0]
    return np.sum(psd[alfa_idx])

def detectar_picos_r(ecg_data, fs):
    # Filtro de fase cero
    ecg_filtrado = bandpass_filter(ecg_data, 5.0, 15.0, fs, order=3)
    
    # Buscamos picos en la señal original (o filtrada) buscando los máximos locales
    # height: altura mínima, distance: distancia mínima entre latidos (ej. 400ms)
    picos, _ = find_peaks(ecg_filtrado, height=np.max(ecg_filtrado)*0.5, distance=int(0.4 * fs))
    
    return picos

def calcular_metricas_ecg(ecg_data, fs):
    """Calcula las variables temporales y espectrales (HRV) directamente desde el filtro Fase Cero"""
    
    # 1. Obtenemos los picos directamente del filtro perfecto (filtfilt)
    picos = detectar_picos_r(ecg_data, fs)
    
    if len(picos) < 3:
        return 0.0, 1.0, 70.0, picos
    
    # 2. Cálculos matemáticos de HRV (Ahora con datos limpios)
    rr_intervals = np.diff(picos) / fs
    bpm = 60.0 / np.mean(rr_intervals)
    
    diff_rr = np.diff(rr_intervals)
    rmssd = np.sqrt(np.mean(diff_rr**2)) * 1000
    
    hf_est = np.std(diff_rr) if len(diff_rr) > 1 else 0.01
    lf_est = np.std(rr_intervals)
    lf_hf = (lf_est / hf_est) if hf_est > 0 else 1.0
    
    return rmssd, lf_hf, bpm, picos

# ==========================================
# 3. INTERFAZ GRÁFICA DE USUARIO (GUI)
# ==========================================
class AcqAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador en Tiempo Real - Biofeedback Estrés")
        self.geometry("1150x720")
        self.configure(bg="#1a1a1a")
        
        self.fs = 1000
        self.eeg_signal = None
        self.ecg_signal = None
        self.total_samples = 0
        self.current_index = 0
        self.is_playing = False
        
        # Listas para guardar las referencias medias basales
        self.alfa_basal = []
        self.lfhf_basal = []
        
        # Historial para el tacograma
        self.historico_tiempos_rr = []
        self.historico_intervalos_rr = []
        
        self.setup_ui()

    def setup_ui(self):
        # Contenedor Izquierdo (Controles y Métricas)
        left_frame = tk.Frame(self, bg="#1a1a1a", width=360)
        left_frame.pack(side="left", fill="y", padx=15, pady=15)
        left_frame.pack_propagate(False)

        title = tk.Label(left_frame, text="SISTEMA DE BIOFEEDBACK\nCONTROL DEL ESTRÉS (ECG+EEG)", font=("Helvetica", 11, "bold"), fg="#ffffff", bg="#1a1a1a")
        title.pack(pady=10)
        
        btn_load = tk.Button(left_frame, text="Cargar Archivo .acq", command=self.cargar_archivo, font=("Helvetica", 11, "bold"), fg="#ffffff", bg="#0275d8", bd=0, padx=15, pady=8)
        btn_load.pack(pady=10)
        
        self.lbl_file = tk.Label(left_frame, text="Ningún archivo seleccionado", font=("Helvetica", 9, "italic"), fg="#888888", bg="#1a1a1a")
        self.lbl_file.pack()

        # --- PANEL DE EXTRACCIÓN DE CARACTERÍSTICAS ---
        panel_datos = tk.LabelFrame(left_frame, text=" Métricas Extraídas (Ventana 2s) ", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1a1a1a", bd=2, padx=10, pady=10)
        panel_datos.pack(pady=15, fill="x")
        
        self.lbl_tiempo = tk.Label(panel_datos, text="Tiempo: 0.0 s", font=("Helvetica", 11, "bold"), fg="#5cb85c", bg="#1a1a1a")
        self.lbl_tiempo.pack(pady=4, anchor="w")
        
        self.lbl_bpm = tk.Label(panel_datos, text="Frecuencia Cardíaca: -- BPM", font=("Helvetica", 11), fg="#dddddd", bg="#1a1a1a")
        self.lbl_bpm.pack(pady=4, anchor="w")
        
        self.lbl_rmssd = tk.Label(panel_datos, text="RMSSD (HRV Temporal): -- ms", font=("Helvetica", 11), fg="#dddddd", bg="#1a1a1a")
        self.lbl_rmssd.pack(pady=4, anchor="w")
        
        self.lbl_lfhf = tk.Label(panel_datos, text="Relación LF/HF (HRV Frec.): --", font=("Helvetica", 11), fg="#dddddd", bg="#1a1a1a")
        self.lbl_lfhf.pack(pady=4, anchor="w")
        
        self.lbl_alfa = tk.Label(panel_datos, text="Potencia Banda Alfa (EEG): --", font=("Helvetica", 11), fg="#dddddd", bg="#1a1a1a")
        self.lbl_alfa.pack(pady=4, anchor="w")

        # --- INDICADOR VISUAL (SEMÁFORO REQUERIDO) ---
        panel_semaforo = tk.LabelFrame(left_frame, text=" Semáforo de Relajación Automatizado ", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1a1a1a", bd=2)
        panel_semaforo.pack(pady=10, fill="x")
        
        self.canvas_semaforo = tk.Canvas(panel_semaforo, width=90, height=90, bg="#262626", highlightthickness=0)
        self.canvas_semaforo.pack(pady=5)
        self.circulo_estado = self.canvas_semaforo.create_oval(10, 10, 80, 80, fill="gray")
        
        self.lbl_estado = tk.Label(panel_semaforo, text="ESPERANDO ARCHIVO...", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#1a1a1a")
        self.lbl_estado.pack(pady=5)

        # Contenedor Derecho (Los 3 Gráficos Simultáneos)
        right_frame = tk.Frame(self, bg="#262626")
        right_frame.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.fig = Figure(figsize=(7, 8), dpi=100, facecolor="#262626")
        
        self.ax_eeg = self.fig.add_subplot(311)
        self.ax_ecg = self.fig.add_subplot(312)
        self.ax_tach = self.fig.add_subplot(313)
        
        for ax in [self.ax_eeg, self.ax_ecg, self.ax_tach]:
            ax.set_facecolor("#1a1a1a")
            ax.tick_params(colors='white', labelsize=8)
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.grid(True, color="#333333", linestyle="--")

        self.fig.tight_layout(pad=3.0)
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas_plot.get_tk_widget().pack(fill="both", expand=True)

    def cargar_archivo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos BIOPAC", "*.acq")])
        if not file_path:
            return
        
        try:
            self.lbl_file.config(text=os.path.basename(file_path))
            data_acq = bioread.read(file_path)
            self.fs = data_acq.samples_per_second
            
            # Canal 1 (Índice 0): EEG (Fz/Cz)
            # Canal 2 (Índice 1): ECG (Derivación II)
            self.eeg_signal = data_acq.channels[0].data
            self.ecg_signal = data_acq.channels[1].data
            
            self.total_samples = len(self.ecg_signal)
            self.current_index = 0
            self.is_playing = True
            
            # Limpieza de historiales
            self.historico_tiempos_rr.clear()
            self.historico_intervalos_rr.clear()
            self.alfa_basal.clear()
            self.lfhf_basal.clear()
            
            self.lbl_estado.config(text="PROCESANDO...", fg="#ffffff")
            self.procesar_siguiente_bloque()
            
        except Exception as e:
            messagebox.showerror("Error de lectura", f"Error al procesar con bioread:\n{str(e)}")

    def procesar_siguiente_bloque(self):
        if not self.is_playing:
            return
            
        samples_window = int(WINDOW_SEC * self.fs)
        if self.current_index + samples_window > self.total_samples:
            self.is_playing = False
            self.lbl_estado.config(text="ANÁLISIS FINALIZADO", fg="#0275d8")
            return
            
        start_idx = self.current_index
        end_idx = start_idx + samples_window
        
        block_eeg = self.eeg_signal[start_idx:end_idx]
        block_ecg = self.ecg_signal[start_idx:end_idx]
        
        tiempo_actual = end_idx / self.fs
        self.lbl_tiempo.config(text=f"Tiempo: {tiempo_actual:.1f} s / {self.total_samples/self.fs:.1f} s")
        
        # Procesamiento matemático de señales
        potencia_alfa = calcular_potencia_alfa(block_eeg, self.fs)
        rmssd, lf_hf, bpm, picos_locales = calcular_metricas_ecg(block_ecg, self.fs)
        
        # Guardado y cálculo acumulativo del Tacograma
        if len(picos_locales) > 1:
            tiempos_picos_globales = (start_idx + picos_locales) / self.fs
            intervalos_rr = np.diff(tiempos_picos_globales) * 1000 # Pasar a ms
            
            for t, rr in zip(tiempos_picos_globales[1:], intervalos_rr):
                if len(self.historico_tiempos_rr) == 0 or t > self.historico_tiempos_rr[-1]:
                    self.historico_tiempos_rr.append(t)
                    self.historico_intervalos_rr.append(rr)

        # Actualización de Métricas en el Panel
        self.lbl_bpm.config(text=f"Frecuencia Cardíaca: {bpm:.1f} BPM")
        self.lbl_rmssd.config(text=f"RMSSD (HRV): {rmssd:.1f} ms")
        self.lbl_alfa.config(text=f"Potencia Banda Alfa: {potencia_alfa:.4f}")
        self.lbl_lfhf.config(text=f"Relación LF/HF: {lf_hf:.2f}")
        
        # LÓGICA BIOMÉDICA DEL SEMÁFORO (Coincidencia Bimodal Solicitada)
        # Se toma el promedio de los primeros 10 segundos como Línea Base Calma.
        if tiempo_actual <= 10.0:
            self.alfa_basal.append(potencia_alfa)
            self.lfhf_basal.append(lf_hf)
            self.canvas_semaforo.itemconfig(self.circulo_estado, fill="gray")
            self.lbl_estado.config(text="CALIBRANDO LÍNEA BASE...", fg="#ffffff")
        else:
            umbral_alfa = np.median(self.alfa_basal) * 0.85
            umbral_lfhf = np.median(self.lfhf_basal) * 1.15
            
            # Evaluación fisiológica combinada
            if potencia_alfa >= umbral_alfa and lf_hf <= umbral_lfhf:
                self.canvas_semaforo.itemconfig(self.circulo_estado, fill="#4caf50")
                self.lbl_estado.config(text="ESTADO: RELAJACIÓN (CALMA)", fg="#4caf50")
            else:
                self.canvas_semaforo.itemconfig(self.circulo_estado, fill="#f44336")
                self.lbl_estado.config(text="ESTADO: ALERTA / ESTRÉS", fg="#f44336")
            
        # --- ACTUALIZACIÓN DE LAS GRÁFICAS REQUERIDAS ---
        time_vector = np.linspace(start_idx / self.fs, end_idx / self.fs, len(block_eeg))
        
        # 1. Canal 1: EEG
        self.ax_eeg.clear()
        self.ax_eeg.plot(time_vector, block_eeg, color="#2ecc71", linewidth=0.8)
        self.ax_eeg.set_title("Canal 1: Señal EEG (Fz/Cz)", fontsize=9)
        self.ax_eeg.set_ylabel("Voltaje (uV)")
        
        # 2. Canal 2: ECG con Picos R Detectados
        self.ax_ecg.clear()
        self.ax_ecg.plot(time_vector, block_ecg, color="#e74c3c", linewidth=0.8)
        if len(picos_locales) > 0:
            self.ax_ecg.scatter(time_vector[picos_locales], block_ecg[picos_locales], color="white", edgecolors="black", s=35, zorder=3)
        self.ax_ecg.set_title("Canal 2: Señal ECG (Derivación II) + Picos R", fontsize=9)
        self.ax_ecg.set_ylabel("Voltaje (mV)")
        
        # 3. Tacograma Acumulativo de Intervalos R-R
        self.ax_tach.clear()
        if len(self.historico_tiempos_rr) > 0:
            self.ax_tach.plot(self.historico_tiempos_rr, self.historico_intervalos_rr, color="#f1c40f", marker="o", markersize=2.5, linestyle="-", linewidth=1)
        self.ax_tach.set_title("Tacograma de Intervalos R-R (Evolutivo)", fontsize=9)
        self.ax_tach.set_xlabel("Tiempo General de Registro (s)")
        self.ax_tach.set_ylabel("Intervalo R-R (ms)")
        
        # Restaurar grillas estéticas en la recarga
        for ax in [self.ax_eeg, self.ax_ecg, self.ax_tach]:
            ax.grid(True, color="#333333", linestyle="--")
            
        self.canvas_plot.draw()

        # Ciclo multitarea mediante .after sin congelar el hilo principal de la GUI
        self.current_index += int((UPDATE_MS / 1000) * self.fs)
        self.after(UPDATE_MS, self.procesar_siguiente_bloque)

if __name__ == "__main__":
    app = AcqAnalysisApp()
    app.mainloop()