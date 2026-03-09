import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SymulatorStacji:
    def __init__(self, liczba_kanalow, lambd, N, sigma, min_czas, maks_czas, max_kolejka, czas_symulacji):
        self.liczba_kanalow = liczba_kanalow
        self.lambd = lambd
        self.N = N
        self.sigma = sigma
        self.min_czas = min_czas
        self.maks_czas = maks_czas
        self.max_kolejka = max_kolejka
        self.czas_symulacji = czas_symulacji

        self.kanaly = []
        self.kolejka = []
        self.odrzuceni = 0
        self.obsluzeni = 0
        self.aktualny_krok = 0

        self.historia_rho, self.historia_Q, self.historia_W = [], [], []

        self.czasy_przyjsc = []
        self.czasy_obslugi = []
        self.klienci_dane = []
        self.suma_czasow_obslugi = 0

        self.u_poisson = 0
        self.t_poisson = 0
        self.u1_gauss = 0
        self.u2_gauss = 0
        self.x_gauss = 0

        self.generuj_zdarzenia()

        with open("Wyniki.txt", "w", encoding="utf-8") as f:
            f.write(f"{'Krok (s)':<10} | {'Kolejka (Q)':<12} | {'Czas Oczek. (W)':<16} | {'Ro (Zajętość)':<14} | {'Obsłużeni':<10} | {'Odrzuceni':<10}\n")
            f.write("-" * 85 + "\n")

    def generuj_zdarzenia(self):
        czas_abs = 0
        id_klienta = 1
        while czas_abs < self.czas_symulacji:
            u = np.random.rand()
            odstep = -np.log(u) / self.lambd
            czas_abs += odstep
            self.u_poisson = u
            self.t_poisson = odstep
            if czas_abs <= self.czas_symulacji:
                self.czasy_przyjsc.append(czas_abs)
                u1, u2 = np.random.rand(), np.random.rand()
                z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
                czas_rozmowy = self.N + self.sigma * z0
                czas_rozmowy = max(self.min_czas, min(czas_rozmowy, self.maks_czas))
                self.u1_gauss = u1
                self.u2_gauss = u2
                self.x_gauss = czas_rozmowy
                self.czasy_obslugi.append(czas_rozmowy)
                self.suma_czasow_obslugi += czas_rozmowy
                b_lambda_i = id_klienta / czas_abs
                b_mi_i = id_klienta / self.suma_czasow_obslugi
                b_ro_i = b_lambda_i / b_mi_i if b_mi_i > 0 else 0
                self.klienci_dane.append({
                    "id": id_klienta, "poisson": round(u, 4), "gauss": int(czas_rozmowy),
                    "czas_przyjscia": int(czas_abs), "czas_obslugi": int(self.suma_czasow_obslugi),
                    "lambdai": round(b_lambda_i, 3), "mii": round(b_mi_i, 3), "roi": round(b_ro_i, 3)
                })
                id_klienta += 1

    def wykonaj_sekunde(self):
        if self.aktualny_krok >= self.czas_symulacji:
            return False, []
        for i in range(len(self.kanaly) - 1, -1, -1):
            self.kanaly[i] -= 1
            if self.kanaly[i] <= 0:
                self.kanaly.pop(i)
                self.obsluzeni += 1
        while len(self.kanaly) < self.liczba_kanalow and len(self.kolejka) > 0:
            self.kanaly.append(self.kolejka.pop(0))
        nowi_klienci = []
        while len(self.czasy_przyjsc) > 0 and self.czasy_przyjsc[0] <= self.aktualny_krok:
            self.czasy_przyjsc.pop(0)
            czas_rozm = self.czasy_obslugi.pop(0)
            if len(self.klienci_dane) > 0:
                nowi_klienci.append(self.klienci_dane.pop(0))
            if len(self.kanaly) < self.liczba_kanalow:
                self.kanaly.append(czas_rozm)
            elif len(self.kolejka) < self.max_kolejka:
                self.kolejka.append(czas_rozm)
            else:
                self.odrzuceni += 1
        rho = len(self.kanaly) / self.liczba_kanalow if self.liczba_kanalow > 0 else 0
        Q = len(self.kolejka)
        W = Q / self.lambd if self.lambd > 0 else 0
        self.historia_rho.append(rho)
        self.historia_Q.append(Q)
        self.historia_W.append(W)
        with open("Wyniki.txt", "a", encoding="utf-8") as f:
            f.write(f"{self.aktualny_krok:<10} | {Q:<12} | {round(W,4):<16} | {round(rho,4):<14} | {self.obsluzeni:<10} | {self.odrzuceni:<10}\n")
        self.aktualny_krok += 1
        return True, nowi_klienci


class AplikacjaGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1450x900")
        self.root.configure(bg="#e8e8e8")

        self.symulator = None
        self.dziala = False
        self.buduj_interfejs()

    def buduj_interfejs(self):

        self.top_container = ttk.Frame(self.root)
        self.top_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.bottom_container = ttk.Frame(self.root)
        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


        self.left_panel = ttk.Frame(self.top_container)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.center_panel = ttk.Frame(self.top_container)
        self.center_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.right_panel = ttk.Frame(self.top_container)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)


        lf_parametry = ttk.LabelFrame(self.left_panel, text=" Konfiguracja Systemu ")
        lf_parametry.pack(fill=tk.X, pady=5)

        self.pola = {}
        parametry_def = [
            ("Liczba kanałów", 10, ""), ("Długość kolejki", 10, ""),
            ("Natężenie ruchu [lambda]", 1.0, ""), ("Średnia długość rozmowy", 20, "[s]"),
            ("Odchylenie standardowe", 5, ""), ("Minimalny czas połączenia", 10, "[s]"),
            ("Maksymalny czas połączenia", 30, "[s]"), ("Czas symulacji", 30, "[s]")
        ]

        for i, (nazwa, wart, jednostka) in enumerate(parametry_def):
            ttk.Label(lf_parametry, text=nazwa).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value=str(wart))
            ttk.Entry(lf_parametry, textvariable=var, width=8, justify="center").grid(row=i, column=1, padx=5, pady=2)
            ttk.Label(lf_parametry, text=jednostka).grid(row=i, column=2, sticky=tk.W)
            self.pola[nazwa] = var


        lf_geny = ttk.LabelFrame(self.left_panel, text=" Generator Zmiennych ")
        lf_geny.pack(fill=tk.X, pady=5)


        f_poi = ttk.Frame(lf_geny); f_poi.pack(pady=5)
        ttk.Label(f_poi, text="Poisson X:").grid(row=0, column=0, padx=2)
        self.var_poisson_x = tk.StringVar()
        ttk.Entry(f_poi, textvariable=self.var_poisson_x, width=10, state='readonly').grid(row=0, column=1, padx=2)
        ttk.Label(f_poi, text="Licznik λi:").grid(row=0, column=2, padx=2)
        self.var_poisson_l = tk.StringVar()
        ttk.Entry(f_poi, textvariable=self.var_poisson_l, width=10, state='readonly').grid(row=0, column=3, padx=2)


        f_gau = ttk.Frame(lf_geny); f_gau.pack(pady=5)
        ttk.Label(f_gau, text="Gauss X1:").grid(row=0, column=0, padx=2)
        self.var_gauss_x1 = tk.StringVar()
        ttk.Entry(f_gau, textvariable=self.var_gauss_x1, width=8, state='readonly').grid(row=0, column=1, padx=2)
        ttk.Label(f_gau, text="X2:").grid(row=0, column=2, padx=2)
        self.var_gauss_x2 = tk.StringVar()
        ttk.Entry(f_gau, textvariable=self.var_gauss_x2, width=8, state='readonly').grid(row=0, column=3, padx=2)
        ttk.Label(f_gau, text="Wynik X:").grid(row=0, column=4, padx=2)
        self.var_gauss_x = tk.StringVar()
        ttk.Entry(f_gau, textvariable=self.var_gauss_x, width=8, state='readonly').grid(row=0, column=5, padx=2)


        self.frame_ctrl = ttk.Frame(self.center_panel)
        self.frame_ctrl.pack(fill=tk.X, pady=5)

        tk.Button(self.frame_ctrl, text="START SYMULACJI", bg="#2ecc71", fg="white", font=("Arial", 11, "bold"), command=self.start_symulacji).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(self.frame_ctrl, text="Pause", command=self.pauza, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(self.frame_ctrl, text="Play", command=self.wznow, width=8).pack(side=tk.LEFT, padx=2)

        self.lf_kanaly_box = ttk.LabelFrame(self.center_panel, text=" Status Kanałów Obsługi ")
        self.lf_kanaly_box.pack(fill=tk.BOTH, expand=True, pady=5)

        self.frame_kanaly = tk.Frame(self.lf_kanaly_box, bg="#e8e8e8")
        self.frame_kanaly.pack(pady=10, padx=10)
        self.kanaly_lbl = []


        lf_stats = ttk.LabelFrame(self.center_panel, text=" Statystyki Bieżące ")
        lf_stats.pack(fill=tk.X, pady=5)

        self.pb_kolejka = ttk.Progressbar(lf_stats, orient="horizontal", length=250, mode="determinate")
        self.pb_kolejka.pack(pady=10, padx=10)
        self.lbl_kolejka = ttk.Label(lf_stats, text="Kolejka: 0 / 10", font=("Arial", 10, "bold"))
        self.lbl_kolejka.pack()

        self.lbl_obsluzone = ttk.Label(lf_stats, text="Obsłużone: 0")
        self.lbl_obsluzone.pack(pady=2)
        self.lbl_odrzucone = ttk.Label(lf_stats, text="Odrzucone: 0")
        self.lbl_odrzucone.pack(pady=2)
        self.lbl_czas_nast = ttk.Label(lf_stats, text="Następne połączenie za: 0s")
        self.lbl_czas_nast.pack(pady=2)

        self.lbl_czas = ttk.Label(self.center_panel, text="CZAS: 0 / 30", font=("Arial", 14, "bold"))
        self.lbl_czas.pack(pady=20)


        self.fig = Figure(figsize=(6, 8), dpi=90)
        self.ax_q = self.fig.add_subplot(311)
        self.ax_w = self.fig.add_subplot(312)
        self.ax_ro = self.fig.add_subplot(313)
        self.fig.subplots_adjust(hspace=0.6, left=0.15, right=0.95, top=0.95, bottom=0.08)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        f_av_stats = ttk.Frame(self.right_panel)
        f_av_stats.pack(fill=tk.X)
        self.lbl_avg_q = ttk.Label(f_av_stats, text="Śr. Q: 0")
        self.lbl_avg_q.pack(side=tk.LEFT, expand=True)
        self.lbl_avg_w = ttk.Label(f_av_stats, text="Śr. W: 0")
        self.lbl_avg_w.pack(side=tk.LEFT, expand=True)
        self.lbl_avg_ro = ttk.Label(f_av_stats, text="Ro: 0")
        self.lbl_avg_ro.pack(side=tk.LEFT, expand=True)


        lf_tabela = ttk.LabelFrame(self.bottom_container, text=" Log Zdarzeń i Obliczeń ")
        lf_tabela.pack(fill=tk.BOTH, expand=True)

        self.var_pokaz = tk.BooleanVar(value=True)
        tk.Checkbutton(lf_tabela, text="Odświeżaj wykresy w czasie rzeczywistym", variable=self.var_pokaz, bg="#e8e8e8").pack(anchor=tk.W)

        scroll = ttk.Scrollbar(lf_tabela)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        kolumny = ("Pois", "Gauss", "Klient", "T_Przy", "T_Obs", "lambdai", "Mii", "Roi")
        self.tabela = ttk.Treeview(lf_tabela, columns=kolumny, show='headings', height=8, yscrollcommand=scroll.set)
        for col in kolumny:
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=100, anchor=tk.CENTER)
        self.tabela.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.tabela.yview)

   
    def start_symulacji(self):
        try:
            l_kanalow = int(self.pola["Liczba kanałów"].get())
            l_kolejka = int(self.pola["Długość kolejki"].get())
            lambd = float(self.pola["Natężenie ruchu [lambda]"].get())
            N = float(self.pola["Średnia długość rozmowy"].get())
            sigma = float(self.pola["Odchylenie standardowe"].get())
            min_c = float(self.pola["Minimalny czas połączenia"].get())
            max_c = float(self.pola["Maksymalny czas połączenia"].get())
            czas_sym = int(self.pola["Czas symulacji"].get())
        except ValueError:
            messagebox.showerror("Błąd", "Niepoprawne parametry!")
            return

        for w in self.frame_kanaly.winfo_children(): w.destroy()
        self.kanaly_lbl = []
        for i in range(l_kanalow):
            lbl = tk.Label(self.frame_kanaly, text="", bg="#27ae60", fg="white", font=("Arial", 11, "bold"), width=7, height=2, relief="raised", bd=2)
            lbl.grid(row=i//5, column=i%5, padx=3, pady=3)
            self.kanaly_lbl.append(lbl)

        self.pb_kolejka["maximum"] = l_kolejka
        for item in self.tabela.get_children(): self.tabela.delete(item)

        self.symulator = SymulatorStacji(l_kanalow, lambd, N, sigma, min_c, max_c, l_kolejka, czas_sym)

        self.var_poisson_x.set(round(self.symulator.u_poisson, 5))
        self.var_poisson_l.set(round(self.symulator.t_poisson, 5))
        self.var_gauss_x1.set(round(self.symulator.u1_gauss, 5))
        self.var_gauss_x2.set(round(self.symulator.u2_gauss, 5))
        self.var_gauss_x.set(int(self.symulator.x_gauss))

        self.dziala = True
        self.ax_q.clear(); self.ax_w.clear(); self.ax_ro.clear()
        self.canvas.draw()
        self.petla_symulacji()

    def pauza(self): self.dziala = False
    def wznow(self):
        if not self.dziala and self.symulator and self.symulator.aktualny_krok < self.symulator.czas_symulacji:
            self.dziala = True
            self.petla_symulacji()

    def petla_symulacji(self):
        if not self.dziala: return
        trwa, nowi_klienci = self.symulator.wykonaj_sekunde()
        if trwa:
            self.aktualizuj_gui(nowi_klienci)
            self.root.after(300, self.petla_symulacji)
        else: self.dziala = False

    def aktualizuj_gui(self, nowi_klienci):
        for k in nowi_klienci:
            self.tabela.insert('', tk.END, values=(k["poisson"], k["gauss"], k["id"], k["czas_przyjscia"], k["czas_obslugi"], k["lambdai"], k["mii"], k["roi"]))
            self.tabela.yview_moveto(1)

        for i in range(self.symulator.liczba_kanalow):
            if i < len(self.symulator.kanaly):
                self.kanaly_lbl[i].config(bg="#e74c3c", text=str(int(self.symulator.kanaly[i])))
            else:
                self.kanaly_lbl[i].config(bg="#27ae60", text="")

        q_len = len(self.symulator.kolejka)
        self.pb_kolejka["value"] = q_len
        self.lbl_kolejka.config(text=f"Kolejka: {q_len} / {self.symulator.max_kolejka}")
        self.lbl_obsluzone.config(text=f"Obsłużone: {self.symulator.obsluzeni}")
        self.lbl_odrzucone.config(text=f"Odrzucone: {self.symulator.odrzuceni}")
        self.lbl_czas.config(text=f"CZAS: {self.symulator.aktualny_krok} / {self.symulator.czas_symulacji}")

        czas_do_nast = max(0, int(self.symulator.czasy_przyjsc[0] - self.symulator.aktualny_krok)) if self.symulator.czasy_przyjsc else 0
        self.lbl_czas_nast.config(text=f"Następne połączenie za: {czas_do_nast}s")

        if self.var_pokaz.get():
            self.ax_q.clear(); self.ax_w.clear(); self.ax_ro.clear()
            x_data = list(range(len(self.symulator.historia_Q)))
            self.ax_q.step(x_data, self.symulator.historia_Q, color='#e74c3c', label='Kolejka (Q)', where='post')
            self.ax_w.step(x_data, self.symulator.historia_W, color='#3498db', label='Czas oczek. (W)', where='post')
            self.ax_ro.step(x_data, self.symulator.historia_rho, color='#2ecc71', label='Zajętość (Ro)', where='post')

            for ax in (self.ax_q, self.ax_w, self.ax_ro):
                ax.set_xlim(left=0, right=max(10, len(self.symulator.historia_Q)))
                ax.set_ylim(bottom=0)
                ax.grid(True, linestyle=':', alpha=0.7)
                ax.legend(loc='upper right', fontsize='small')

            self.canvas.draw()
            avg_q = round(np.mean(self.symulator.historia_Q), 3) if self.symulator.historia_Q else 0
            avg_w = round(np.mean(self.symulator.historia_W), 3) if self.symulator.historia_W else 0
            avg_ro = round(np.mean(self.symulator.historia_rho), 3) if self.symulator.historia_rho else 0
            self.lbl_avg_q.config(text=f"Śr. Q: {avg_q}")
            self.lbl_avg_w.config(text=f"Śr. W: {avg_w}")
            self.lbl_avg_ro.config(text=f"Ro: {avg_ro}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplikacjaGUI(root)
    root.mainloop()