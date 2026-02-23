import math
import time
import matplotlib.pyplot as plt

class MobileSystemsGenerator:
    def __init__(self, seed=None):
        self.a = 16807
        self.b = 0
        self.c = 2147483647
        self.state = seed if seed is not None else int(time.time() % self.c)

    def gen_u_01(self):
        self.state = (self.a * self.state + self.b) % self.c
        return self.state / self.c

    def poisson(self, lam, n_samples):
        results = []
        q = math.exp(-lam)
        for _ in range(n_samples):
            X = -1
            s = 1
            while s > q:
                u = self.gen_u_01()
                s = s * u
                X += 1
            results.append(X)
        return results

    def normal_gauss(self, mu, sigma, n_samples):
        results = []
        while len(results) < n_samples:
            u1 = self.gen_u_01()
            u2 = self.gen_u_01()

            z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            z1 = math.sqrt(-2 * math.log(u1)) * math.sin(2 * math.pi * u2)

            results.append(mu + sigma * z0)
            if len(results) < n_samples:
                results.append(mu + sigma * z1)
        return results

def draw_histogram(data, title, is_discrete=False):
    plt.figure(figsize=(10, 5))
    if is_discrete:
        bins = range(min(data), max(data) + 2)
        plt.hist(data, bins=bins, align='left', rwidth=0.8, color='green', alpha=0.7)
    else:
        plt.hist(data, bins=50, color='blue', alpha=0.7)

    plt.title(title)
    plt.xlabel("Wartość")
    plt.ylabel("Częstość")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

gen = MobileSystemsGenerator(seed=123)
ilosc = 5000

dane_poisson = gen.poisson(lam=4, n_samples=ilosc)
draw_histogram(dane_poisson, f"Histogram: Rozkład Poissona (lambda=4, n={ilosc})", is_discrete=True)

dane_normalny = gen.normal_gauss(mu=0, sigma=1, n_samples=ilosc)
draw_histogram(dane_normalny, f"Histogram: Rozkład Normalny (mu=0, sigma=1, n={ilosc})")