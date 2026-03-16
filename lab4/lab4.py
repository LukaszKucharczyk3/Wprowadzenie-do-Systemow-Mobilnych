import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SymulatorStacji:
    def __init__(self, Liczba_kanalow, lambd, N, sigma, Min, Maks, Dlugosc_kolejki, Czas_symulacji):
        self.Liczba_kanalow, self.lambd, self.N, self.sigma = Liczba_kanalow, lambd, N, sigma
        self.Min, self.Maks, self.Dlugosc_kolejki, self.Czas_symulacji = Min, Maks, Dlugosc_kolejki, Czas_symulacji

        self.kanaly, self.kolejka, self.obsluzeni, self.aktualny_krok = [], [], 0, 0
        self.historia_rho, self.historia_Q, self.historia_W = [], [], []
        self.lambda_i_lista, self.mi_i_lista = [], []

        self.generuj_listy_pary()


        with open("Wyniki.txt", "w", encoding="utf-8") as f:
            f.write(f"PARAMETRY: Kan={Liczba_kanalow}, L={lambd}, N={N}, S={sigma}, Min={Min}, Max={Maks}\n\n")
            f.write(f"{'Krok':<6} | {'rho':<6} | {'Q':<6} | {'W':<6}\n" + "-"*30 + "\n")

    def generuj_listy_pary(self):
        # Generowanie list zdarzeń wg rozkładu Poissona (przybycia) i Gaussa (obsługa)
        suma_lambda = 0
        while suma_lambda < self.Czas_symulacji + 100:
            odstep = -np.log(np.random.rand()) / self.lambd
            suma_lambda += odstep
            self.lambda_i_lista.append(suma_lambda)

            z0 = np.sqrt(-2 * np.log(np.random.rand())) * np.cos(2 * np.pi * np.random.rand())
            dlugosc = max(self.Min, min(self.N + self.sigma * z0, self.Maks))
            self.mi_i_lista.append(dlugosc)

    def wykonaj_krok(self):
        if self.aktualny_krok >= self.Czas_symulacji: return False

        # Zwalnianie kanałów, w których rozmowa dobiegła końca
        for i in range(len(self.kanaly)-1, -1, -1):
            self.kanaly[i] -= 1
            if self.kanaly[i] <= 0:
                self.kanaly.pop(i)
                self.obsluzeni += 1

        # Pobieranie osób z kolejki do wolnych kanałów
        while len(self.kanaly) < self.Liczba_kanalow and self.kolejka:
            self.kanaly.append(self.kolejka.pop(0))

        # Pobranie nowych klientów, których czas przybycia nadszedł w bieżącej sekundzie
        k_do_usun = 0
        for t_przy in self.lambda_i_lista:
            if t_przy <= self.aktualny_krok:
                k_do_usun += 1
                dl_obs = self.mi_i_lista[k_do_usun-1]
                if len(self.kanaly) < self.Liczba_kanalow:
                    self.kanaly.append(dl_obs)
                elif len(self.kolejka) < self.Dlugosc_kolejki:
                    self.kolejka.append(dl_obs)
            else: break

        # Usuwanie przetworzonych zdarzeń z list pierwotnych
        for _ in range(k_do_usun):
            self.lambda_i_lista.pop(0)
            self.mi_i_lista.pop(0)

        # Obliczanie i zapisywanie statystyk kroku
        rho = len(self.kanaly) / self.Liczba_kanalow
        Q = len(self.kolejka)
        W = Q / self.lambd

        self.historia_rho.append(rho)
        self.historia_Q.append(Q)
        self.historia_W.append(W)

        with open("Wyniki.txt", "a") as f:
            f.write(f"{self.aktualny_krok:<6} | {rho:<6.2f} | {Q:<6} | {W:<6.2f}\n")

        self.aktualny_krok += 1
        return True

class AplikacjaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Symulator Stacji Bazowej")
        self.sym, self.dziala = None, False

        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.panel_lewy = ttk.Frame(main_frame)
        self.panel_lewy.pack(side="left", fill="y", padx=5)

        self.pola = {}
        parametry = [("Liczba kanałów", 10), ("Lambda", 1.0), ("N (Śr. rozmowa)", 20),
                     ("Sigma", 5), ("Min", 10), ("Maks", 30),
                     ("Długość kolejki", 10), ("Czas symulacji", 60)]

        for i, (nazwa, domyslna) in enumerate(parametry):
            ttk.Label(self.panel_lewy, text=nazwa).grid(row=i, column=0, sticky="w")
            var = tk.StringVar(value=str(domyslna))
            ttk.Entry(self.panel_lewy, textvariable=var, width=10).grid(row=i, column=1, pady=2)
            self.pola[nazwa] = var

        ttk.Button(self.panel_lewy, text="START SYMULACJI", command=self.start).grid(row=8, column=0, columnspan=2, pady=10)

        self.lbl_stats = ttk.LabelFrame(self.panel_lewy, text=" Wyniki Symulacji ")
        self.lbl_stats.grid(row=9, column=0, columnspan=2, sticky="ew", pady=5)

        self.res_krok = ttk.Label(self.lbl_stats, text="Czas: 0"); self.res_krok.pack(anchor="w")
        self.res_obs = ttk.Label(self.lbl_stats, text="Obsłużeni: 0"); self.res_obs.pack(anchor="w")
        self.res_rho = ttk.Label(self.lbl_stats, text="Bieżące rho: 0.00"); self.res_rho.pack(anchor="w")
        self.res_q = ttk.Label(self.lbl_stats, text="Średnie Q: 0.00"); self.res_q.pack(anchor="w")
        self.res_w = ttk.Label(self.lbl_stats, text="Średnie W: 0.00"); self.res_w.pack(anchor="w")

        self.ramka_kanaly = ttk.Frame(self.panel_lewy)
        self.ramka_kanaly.grid(row=11, column=0, columnspan=2, pady=10)
        self.labele_kanalow = []

        self.panel_prawy = ttk.Frame(main_frame)
        self.panel_prawy.pack(side="right", fill="both", expand=True)

        self.fig = Figure(figsize=(5, 7), dpi=80)
        self.ax_rho = self.fig.add_subplot(311); self.ax_Q = self.fig.add_subplot(312); self.ax_W = self.fig.add_subplot(313)
        self.canvas = FigureCanvasTkAgg(self.fig, self.panel_prawy)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def start(self):
        try:
            p = {n: float(v.get()) for n, v in self.pola.items()}
            self.sym = SymulatorStacji(int(p["Liczba kanałów"]), p["Lambda"], p["N (Śr. rozmowa)"],
                                       p["Sigma"], p["Min"], p["Maks"],
                                       int(p["Długość kolejki"]), int(p["Czas symulacji"]))

            for w in self.ramka_kanaly.winfo_children(): w.destroy()
            self.labele_kanalow = [tk.Label(self.ramka_kanaly, text="", bg="green", width=4, relief="ridge") for _ in range(self.sym.Liczba_kanalow)]
            for i, lbl in enumerate(self.labele_kanalow): lbl.grid(row=i//5, column=i%5, padx=1, pady=1)

            self.dziala = True
            self.petla()
        except Exception:
            messagebox.showerror("Błąd", "Wprowadź poprawne liczby.")

    def petla(self):
        # Główna pętla sterująca GUI i odświeżaniem wykresów co krok czasu
        if not self.dziala: return

        if self.sym.wykonaj_krok():
            self.res_krok.config(text=f"Czas: {self.sym.aktualny_krok} / {self.sym.Czas_symulacji}")
            self.res_obs.config(text=f"Obsłużeni: {self.sym.obsluzeni}")
            self.res_rho.config(text=f"Bieżące rho: {self.sym.historia_rho[-1]:.2f}")
            self.res_q.config(text=f"Średnie Q: {np.mean(self.sym.historia_Q):.2f}")
            self.res_w.config(text=f"Średnie W: {np.mean(self.sym.historia_W):.2f}")

            for i in range(self.sym.Liczba_kanalow):
                if i < len(self.sym.kanaly):
                    self.labele_kanalow[i].config(bg="red", text=int(self.sym.kanaly[i]))
                else:
                    self.labele_kanalow[i].config(bg="green", text="")

            for ax, dane, tytul, kolor in zip([self.ax_rho, self.ax_Q, self.ax_W],
                                              [self.sym.historia_rho, self.sym.historia_Q, self.sym.historia_W],
                                              ["rho - Intensywność", "Q - Długość kolejki", "W - Czas oczekiwania"], ["g", "r", "b"]):
                ax.clear()
                ax.step(range(len(dane)), dane, color=kolor)
                ax.set_title(tytul, fontsize=9)

            self.fig.tight_layout()
            self.canvas.draw()
            self.root.after(300, self.petla)
        else:
            self.dziala = False
            messagebox.showinfo("Koniec", "Symulacja zakończona wyniki w pliku Wyniki.txt.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AplikacjaGUI(root)
    root.mainloop()