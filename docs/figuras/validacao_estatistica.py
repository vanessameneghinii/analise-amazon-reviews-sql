"""Testes estatísticos e figura da seção "O que a análise mostra (e o que não permite concluir)" do README.

O script lê o banco SQLite original (tabela amazon_reviews), imprime os valores citados no README
e grava a figura validacao_com_dados_reais.png ao lado dele.

Dependências: numpy, scipy e matplotlib (pip install numpy scipy matplotlib).

Uso, de qualquer pasta:
    python docs/figuras/validacao_estatistica.py
    python docs/figuras/validacao_estatistica.py --db caminho/do/banco.sqlite --saida figura.png

Por padrão o banco é lido de data/amazon_customer_reviews_100k.sqlite (em modo somente leitura).
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
from scipy import stats  # noqa: E402

AQUI = Path(__file__).resolve().parent
DB_PADRAO = AQUI.parents[1] / "data" / "amazon_customer_reviews_100k.sqlite"
SAIDA_PADRAO = AQUI / "validacao_com_dados_reais.png"

AZUL, LARANJA, CINZA = "#0072B2", "#D55E00", "#8C8C8C"
FRASE_BAIXAS = "Not worth the price."


def virgula(v: float, casas: int) -> str:
    return f"{v:.{casas}f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def carregar(db: Path) -> dict:
    conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
    try:
        linhas = conn.execute(
            "SELECT star_rating, category, strftime('%Y-%m', review_date), review_text FROM amazon_reviews"
        ).fetchall()
    finally:
        conn.close()
    textos = [(l[3] or "") for l in linhas]
    return {
        "nota": np.array([l[0] for l in linhas]),
        "categoria": np.array([l[1] for l in linhas]),
        "mes": np.array([l[2] for l in linhas]),
        "texto": textos,
        "worth": np.array(["worth" in t.lower() for t in textos]),
    }


# ---------------------------------------------------------------------------
# Cálculos (imprime os valores usados no README e devolve o que a figura precisa)
# ---------------------------------------------------------------------------
def calcular(d: dict) -> dict:
    nota, cat, mes, worth, texto = d["nota"], d["categoria"], d["mes"], d["worth"], d["texto"]
    n_total = len(nota)
    mu, dp = float(nota.mean()), float(nota.std(ddof=1))
    print(f"Registros: {n_total}  |  nota média: {mu:.5f}  |  desvio-padrão: {dp:.4f}")

    # 1. Texto e termo "worth"
    det = nota <= 2
    termina = sum(1 for t, e in zip(texto, det) if e and t.endswith(FRASE_BAIXAS))
    altas_com_not_worth = sum(1 for t, e in zip(texto, det) if (not e) and "not worth" in t.lower())
    print("\n[Texto e termo 'worth']")
    print(f"textos distintos: {len(set(texto))} em {n_total} avaliações")
    print(f"avaliações de nota 1 ou 2: {int(det.sum())} | terminam com '{FRASE_BAIXAS}': {termina}")
    print(f"avaliações de nota 3 a 5 que contêm 'not worth': {altas_com_not_worth}")
    print(f"menções a 'worth': {int(worth.sum())} | em notas 1 e 2: {int((worth & det).sum())}")
    pct_worth = {k: 100 * float(worth[nota == k].mean()) for k in range(1, 6)}
    n_nota = {k: int((nota == k).sum()) for k in range(1, 6)}
    print("% com 'worth' por nota:", {k: round(v, 1) for k, v in pct_worth.items()}, "| n por nota:", n_nota)

    # 2. Categorias
    print("\n[Categorias]")
    cats = []
    for k in sorted(set(cat)):
        x = nota[cat == k]
        se = x.std(ddof=1) / math.sqrt(len(x))
        cats.append((str(k), float(x.mean()), float(stats.t.ppf(0.975, len(x) - 1) * se), len(x)))
    cats.sort(key=lambda t: t[1])
    for k, m, h, n in cats:
        print(f"  {k:<16} n={n:>6}  média={m:.4f}  IC95%=[{m - h:.4f}, {m + h:.4f}]")
    print("IC95% de todas as categorias contém a média geral:", all(m - h <= mu <= m + h for _, m, h, _ in cats))
    anova = stats.f_oneway(*[nota[cat == k] for k, *_ in cats])
    print(f"ANOVA entre as {len(cats)} categorias: p = {anova.pvalue:.3f}")
    h, r = nota[cat == "Health"], nota[cat != "Health"]
    print(f"Health contra as demais (Welch): médias {h.mean():.4f} e {r.mean():.4f}, p = {stats.ttest_ind(h, r, equal_var=False).pvalue:.3f}")
    d_h, d_r = int((h <= 2).sum()), int((r <= 2).sum())
    fisher = stats.fisher_exact([[d_h, len(h) - d_h], [d_r, len(r) - d_r]])
    print(f"% de notas 1 e 2: Health {100 * d_h / len(h):.2f}% contra {100 * d_r / len(r):.2f}% (Fisher): p = {fisher[1]:.3f}")

    # 3. Meses
    print("\n[Série mensal]")
    meses = sorted(str(m) for m in set(mes))
    mm = np.array([nota[mes == k].mean() for k in meses])
    nn = np.array([(mes == k).sum() for k in meses])
    meia = 1.96 * dp / np.sqrt(nn)
    fora = [(meses[i], round(float(mm[i]), 3)) for i in range(len(meses)) if abs(mm[i] - mu) > meia[i]]
    i_dez = meses.index("2025-12")
    ordem = sorted(range(len(meses)), key=lambda i: mm[i])
    print(f"meses: {len(meses)} | avaliações por mês, em média: {nn.mean():.0f} | erro-padrão aproximado: {dp / math.sqrt(nn.mean()):.3f}")
    print(f"meses fora de ±1,96 erros-padrão: {len(fora)} {fora} | esperados por acaso: cerca de {0.05 * len(meses):.1f}")
    print(f"2025-12: média {mm[i_dez]:.4f}, posição {ordem.index(i_dez) + 1}º menor de {len(meses)}, dentro da faixa: {abs(mm[i_dez] - mu) <= meia[i_dez]}")
    print(f"2025-02: {mm[meses.index('2025-02')]:.4f} | 2025-08: {mm[meses.index('2025-08')]:.4f}")
    dez25 = nota[mes == "2025-12"]
    outros25 = nota[np.array([m.startswith("2025") and m != "2025-12" for m in mes])]
    print(f"2025-12 contra os demais meses de 2025: {dez25.mean():.4f} e {outros25.mean():.4f}, p = {stats.ttest_ind(dez25, outros25, equal_var=False).pvalue:.3f}")
    eh_dez = np.array([m.endswith("-12") for m in mes])
    print(f"dezembro (11 anos) contra os demais meses: {nota[eh_dez].mean():.4f} e {nota[~eh_dez].mean():.4f}, p = {stats.ttest_ind(nota[eh_dez], nota[~eh_dez], equal_var=False).pvalue:.3f}")

    return {"mu": mu, "pct_worth": pct_worth, "cats": cats, "meses": meses, "mm": mm, "meia": meia, "i_dez": i_dez}


# ---------------------------------------------------------------------------
# Figura
# ---------------------------------------------------------------------------
def desenhar(r: dict, saida: Path) -> None:
    mpl.rcParams.update({
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
        "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out", "axes.grid": False,
    })
    v2 = FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ","))
    mu, meses, mm, meia, i_dez = r["mu"], r["meses"], r["mm"], r["meia"], r["i_dez"]

    fig = plt.figure(figsize=(7.4, 6.0))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.35], height_ratios=[1, 0.95], hspace=0.5, wspace=0.55,
                          left=0.1, right=0.97, top=0.93, bottom=0.09)
    ax_a, ax_b, ax_c = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])

    # (a) percentual de avaliações com "worth", por nota
    ks = [1, 2, 3, 4, 5]
    vals = [r["pct_worth"][k] for k in ks]
    ax_a.bar(ks, vals, color=[LARANJA if v > 0 else AZUL for v in vals], width=0.62)
    for k, v in zip(ks, vals):
        if v == 0:
            ax_a.plot([k], [0], marker="o", ms=4, color=AZUL, clip_on=False, zorder=4)   # barra zero continua visível
    ax_a.text(1.5, 103, "100%", ha="center", va="bottom", fontsize=7, color=LARANJA)
    ax_a.set(ylim=(0, 118), xlim=(0.4, 5.6), xticks=ks, yticks=[0, 50, 100],
             xlabel="Nota da avaliação (estrelas)", ylabel="Avaliações com “worth” (%)")
    ax_a.set_title("“worth” só aparece\nnas notas 1 e 2", loc="left", fontweight="normal")

    # (b) nota média por categoria com intervalo de confiança de 95%
    for y, (k, m, h, _) in enumerate(r["cats"]):
        cor = LARANJA if k == "Health" else AZUL
        ax_b.errorbar(m, y, xerr=h, fmt="o", ms=4, lw=1.1, color=cor, ecolor=cor, capsize=2, zorder=3)
    ax_b.axvline(mu, color=CINZA, ls="--", lw=1, zorder=1)
    ax_b.text(mu + 0.004, len(r["cats"]) - 0.35, f"média geral\n{virgula(mu, 3)}", fontsize=6.5, color=CINZA, va="bottom", ha="left")
    ax_b.set(yticks=range(len(r["cats"])), yticklabels=[k for k, *_ in r["cats"]], ylim=(-0.7, len(r["cats"]) + 0.9),
             xlim=(3.84, 4.04), xticks=[3.85, 3.90, 3.95, 4.00], xlabel="Nota média (intervalo de confiança de 95%)")
    ax_b.xaxis.set_major_formatter(v2)
    ax_b.set_title("Todas as categorias têm médias compatíveis\ncom a média geral", loc="left", fontweight="normal")

    # (c) nota média mensal e faixa esperada ao acaso
    x = np.arange(len(meses))
    ax_c.fill_between(x, mu - meia, mu + meia, color=CINZA, alpha=0.22, lw=0, label="faixa esperada ao acaso (±2 erros-padrão)")
    ax_c.axhline(mu, color=CINZA, lw=0.8)
    ax_c.plot(x, mm, color=AZUL, lw=0.9, marker="o", ms=2.2, zorder=3)
    ax_c.plot([i_dez], [mm[i_dez]], marker="o", ms=5.5, color=LARANJA, zorder=5)
    ax_c.annotate(f"dez/2025: {virgula(mm[i_dez], 2)}", (i_dez, mm[i_dez]), xytext=(i_dez - 17, 3.80), fontsize=7,
                  color=LARANJA, ha="center", va="center",
                  arrowprops=dict(arrowstyle="-", color=LARANJA, lw=0.8, shrinkA=1, shrinkB=3))
    anos = [str(a) for a in range(2015, 2026)]
    ax_c.set(xticks=[meses.index(f"{a}-01") for a in anos], xticklabels=anos, xlim=(-2, len(meses) + 1), ylim=(3.76, 4.14),
             yticks=[3.80, 3.85, 3.90, 3.95, 4.00, 4.05, 4.10], ylabel="Nota média do mês",
             xlabel="Mês da avaliação (janeiro de cada ano)")
    ax_c.yaxis.set_major_formatter(v2)
    ax_c.legend(loc="upper left", frameon=False, handlelength=1.4)
    ax_c.set_title("A média mensal oscila dentro do esperado ao acaso; dez/2025 não destoa", loc="left", fontweight="normal")

    for ax, letra, dx in ((ax_a, "a", -0.2), (ax_b, "b", -0.2), (ax_c, "c", -0.07)):
        ax.text(dx, 1.02, letra, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")

    fig.savefig(saida, dpi=200)
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Testes estatísticos e figura de validação (veja o README).")
    ap.add_argument("--db", type=Path, default=DB_PADRAO, help=f"banco SQLite (padrão: {DB_PADRAO})")
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="arquivo PNG da figura")
    args = ap.parse_args(argv)
    if not args.db.exists():
        print(f"erro: banco não encontrado em {args.db}. Veja data/README.md.", file=sys.stderr)
        return 2
    resultado = calcular(carregar(args.db))
    desenhar(resultado, args.saida)
    print(f"\nFigura gravada em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
