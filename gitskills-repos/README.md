# GitSkills — liczba skilli na repozytorium

Analiza pełnego datasetu [GitSkills](https://huggingface.co/datasets/mvaccargiu/gitskills)
z [MSR Mining Challenge 2027](https://2027.msrconf.org/track/msr-2027-mining-challenge).

Wynik obejmuje **282 200 repozytoriów** i **3 797 117 wystąpień skilli**.
Mediana to **2 skille**, a średnia **13,46 skilla** na repozytorium.
Notebook jest wykonany i zawiera zapisane wyniki oraz trzy wykresy.

Repozytorium zawiera kod, notebook i wyniki agregacji. Surowe dane (13,43 GB)
oraz środowisko `.venv` są lokalne i nie są publikowane w Git.

## Pliki

- `notebooks/skills_per_repository.ipynb` — notebook z agregacją i zapisanymi wynikami.
- `data/gitskills/data/` — pełne cztery tabele w Parquet (około 13,43 GB).
- `data/gitskills/README.md` — oryginalna karta datasetu.
- `data/gitskills/manifest.json` — wersja źródła, rozmiary i sumy kontrolne plików.
- `provenance/gitskills-manifest.json` — opublikowana kopia manifestu użytego pobrania.
- `provenance/DATASET_CARD.md` — karta datasetu z tej samej wersji źródła.
- `results/skills_per_repository.csv` — pełny wynik: `repo_full_name`, `n_skills`.
- `results/skills_per_repository.parquet` — ten sam wynik w Parquet.
- `results/summary.json` — podsumowanie, wersja danych i wyniki walidacji.
- `results/skills_*.png` — trzy wykresy z notebooka: histogram, rozkład skumulowany i 15 największych repozytoriów.

## Uruchomienie

Poniższe polecenia wykonuj w katalogu `gitskills-repos`.
Po przygotowaniu środowiska i danych według instrukcji poniżej notebook otworzysz w PowerShell:

```powershell
.\.venv\Scripts\python.exe -m jupyterlab notebooks/skills_per_repository.ipynb
```

W Jupyter wybierz **Run → Run All Cells**. Można też wykonać notebook bez interfejsu:

```powershell
.\.venv\Scripts\python.exe scripts/execute_notebook.py
.\.venv\Scripts\python.exe scripts/validate_results.py
```

Odtworzenie od zera (Windows, Python 3.12):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe scripts/download_gitskills.py --revision ebab17454a7c236f8f26b183567f1a126f42e3f8
.\.venv\Scripts\python.exe scripts/execute_notebook.py
.\.venv\Scripts\python.exe scripts/validate_results.py
```

`requirements.txt` deklaruje bezpośrednie zależności, a `requirements-lock.txt`
zapisuje dokładne wersje z użytego środowiska. Skrypt pobierający korzysta tylko
z biblioteki standardowej Pythona. Pobiera wszystkie pliki Parquet i kartę datasetu,
wznawia częściowe pobrania, sprawdza rozmiary i sumy SHA-256 publikowane przez Hugging Face
(dla karty datasetu sprawdza hash obiektu Git). Ponowne uruchomienie weryfikuje istniejące pliki.
Dane oraz `.venv` są wyłączone z Git przez `.gitignore`.

## Co oznacza liczba skilli

`n_skills` to liczba różnych ścieżek z tabeli `artifacts` w danym repozytorium.
Każda para `(repo_full_name, path)` stanowi jedno wystąpienie. Kopie identycznej
treści w różnych ścieżkach liczą się osobno. Nie stosujemy filtra `dedup_primary`,
`content_fetched` ani `frontmatter_valid` i nie zliczamy plików pomocniczych
z `artifact_siblings`.

Zgodnie z zakresem źródłowego GitSkills uwzględniamy również warianty nazw, np.
`skill.md` i `coding-skill.md`. Jest to liczba wpisów datasetu, a nie walidacja
semantyczna poprawności każdego skilla.

Agregacja zachowuje wszystkie repozytoria z `repos`, także ewentualne repozytoria
bez artefaktów. Notebook zawiera jedną agregację, podstawowe podsumowanie, trzy wykresy
i eksport wyników. Dodatkowe kontrole kompletności, kluczy i eksportu są w osobnym
skrypcie `scripts/validate_results.py`, który zapisuje `results/summary.json`.
Obliczenia czytają wyłącznie potrzebne kolumny; nie wymagają wczytania treści skilli do RAM.

## Źródło i wersja

- Dataset: `mvaccargiu/gitskills`, snapshot z lipca 2026.
- Commit Hugging Face: `ebab17454a7c236f8f26b183567f1a126f42e3f8`.
- Archiwum: [DOI 10.5281/zenodo.21875637](https://doi.org/10.5281/zenodo.21875637).
- Publikacja: [GitSkills: A Dataset of Agent Skills on GitHub](https://arxiv.org/abs/2608.10906),
  Giuseppe Destefanis, Daniel Graziotin, Matteo Vaccargiu, Marco Ortu.
- Metadane i agregacja datasetu: CC-BY-4.0; zawartość plików zachowuje licencje
  repozytoriów pochodzenia, zgodnie z kartą datasetu.
