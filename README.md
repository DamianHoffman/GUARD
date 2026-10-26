<p align="center">
  <a href="docs/media/guard-demo.mp4">
    <img src="docs/media/guard-demo.gif" alt="GUARD w akcji: 46-sekundowy film pokazujący, jak działa projekt" width="100%">
  </a>
</p>
<p align="center"><sub>▶ Kliknij, aby obejrzeć film w pełnej jakości (MP4, 46 s)</sub></p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/brand/guard-logo-white.svg">
    <img src="docs/assets/brand/guard-logo-black.svg" alt="GUARD" width="320">
  </picture>
</p>

<p align="center"><b>Czyste dane reklamowe. Zaufane raporty.</b></p>

<p align="center">
  <a href="https://github.com/DamianHoffman/guard/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/DamianHoffman/guard/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="PostgreSQL 16" src="https://img.shields.io/badge/PostgreSQL-16-0B0B0C?logo=postgresql&logoColor=white">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-0B0B0C?logo=python&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-0B0B0C?logo=docker&logoColor=white">
  <img alt="Licencja MIT" src="https://img.shields.io/badge/licencja-MIT-0B0B0C">
</p>

---

## Co to jest? Wersja na 30 sekund

Sieci reklamowe codziennie przysyłają pliki z wynikami reklam. Każda **w innym formacie** i **z błędami**.
GUARD **sprawdza te pliki, ładuje dobre dane do bazy i pilnuje, żeby nic się nie zgubiło**, a raporty dla biznesu były wiarygodne.

> To **projekt portfolio** na danych syntetycznych. Pokazuje codzienną pracę juniorskiego DevOpsa:
> baza danych, serwer Linux, automatyzacja, kopie zapasowe, ochrona danych osobowych i obsługa użytkowników biznesowych.

<p align="center"><img src="docs/images/problem-solution.png" alt="Bez GUARD: ręczna praca w Excelu. Z GUARD: automat pilnuje danych." width="100%"></p>

## Jak to działa

<p align="center"><img src="docs/images/how-it-works.png" alt="Cztery kroki: pliki, kontrola, baza, raporty" width="100%"></p>

## Zobacz w akcji

<table>
  <tr>
    <td width="50%"><img src="docs/images/scene-rejects.png" alt="Każdy wiersz jest sprawdzony"><br><b>Każdy wiersz sprawdzony.</b> Błędne trafiają na listę, razem z powodem.</td>
    <td width="50%"><img src="docs/images/scene-privacy.png" alt="Dane osobowe są maskowane"><br><b>Dane osobowe pod kontrolą.</b> Analityk widzi tylko zamaskowaną wersję.</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/images/scene-backups.png" alt="Kopie zapasowe i test odtwarzania"><br><b>Kopie, które da się odtworzyć.</b> Co tydzień automatyczny test.</td>
    <td width="50%"><img src="docs/images/scene-alarm.png" alt="Alarm o brakującym pliku"><br><b>Alarm, zanim zauważy biznes.</b> Brak pliku od sieci reklamowej? Wiadomo od razu.</td>
  </tr>
</table>

## Konsola dla biznesu

Prosta strona **tylko do odczytu**. Nikt nie może z niej niczego zepsuć ani zobaczyć danych osobowych.

<p align="center"><img src="docs/images/console-overview-card.png" alt="Konsola GUARD: przegląd" width="100%"></p>

<table>
  <tr>
    <td width="50%"><img src="docs/images/console-rejects-card.png" alt="Odrzucone wiersze"><br><sub>Odrzucone wiersze, razem z powodem</sub></td>
    <td width="50%"><img src="docs/images/console-status-card.png" alt="Stan systemu"><br><sub>Stan systemu: to samo, co sprawdza dyżurny</sub></td>
  </tr>
</table>

## Jeden dzień z GUARD

<p align="center"><img src="docs/images/day-timeline.png" alt="Harmonogram dnia: kopia o 02:00, ładowanie o 05:30, kontrola o 06:15, kontrola stanu co 10 minut" width="100%"></p>

## Dla kogo?

<p align="center"><img src="docs/images/for-whom.png" alt="Dla rekrutera, działu biznesowego i administratora" width="100%"></p>

## Liczby z przebiegu demo

| | |
|---|---|
| Pliki załadowane | **90** (3 sieci reklamowe, 30 dni) |
| Wiersze sprawdzone | **6 303** |
| Przyjęte do bazy | **6 009** |
| Odrzucone, każdy z powodem | **294** (4,7%) |
| Czas ładowania wszystkiego | **około 0,7 s** |
| Kopia zapasowa + test odtwarzania | **zaszyfrowana, odtworzona w około 1 s** (małe dane demo) |
| Testy automatyczne | **31** (parsowanie, konsola, cały proces ETL) + **12** testów uprawnień |

Dane są generowane względem bieżącej daty, więc przy własnym uruchomieniu liczby będą trochę inne.

## Uruchom u siebie

Potrzebujesz: Python 3.10+, narzędzia PostgreSQL (`psql`, `pg_dump`), `gpg` i Docker (do pełnego zestawu).

```bash
git clone https://github.com/DamianHoffman/guard.git && cd guard
make setup && nano .env     # instalacja polecenia `guard` i ustawienie haseł (ZMIEŃ wszystkie)
make up                     # PostgreSQL, konsola, Grafana, Prometheus
make demo                   # dane demonstracyjne: 30 dni plików, od razu załadowane
make check                  # lint + testy + testy uprawnień
```

Konsola: <http://localhost:8080> · Grafana: <http://localhost:3000> (tylko na Twoim komputerze).
Bez Dockera? Użyj PostgreSQL zainstalowanego na Ubuntu: opis w [`docs/runbook.md`](docs/runbook.md).

| Polecenie | Po co |
|---|---|
| `guard load` | wczytuje pliki z `data/inbox`: sprawdza, przelicza waluty, zapisuje |
| `guard check` | czy każda sieć dostarczyła dzisiejszy plik? |
| `guard health` | kontrola stanu: baza, dysk, kopie, zawieszone zadania |
| `guard backup` / `restore-test` | zaszyfrowana kopia i test jej odtworzenia |
| `guard mask-copy` | kopia bazy z zamaskowanymi danymi osobowymi (dla programistów) |
| `guard console` | uruchamia konsolę webową |
| `guard demo-data …` | generuje dane testowe, także z celowymi awariami do ćwiczeń |

## Architektura

<p align="center"><img src="docs/images/architecture.png" alt="Architektura: sieci reklamowe, GUARD, PostgreSQL, konsola, kopie zapasowe, monitoring" width="100%"></p>

Szczegóły: [`docs/architecture.md`](docs/architecture.md) · decyzje projektowe: [`docs/adr/`](docs/adr/README.md) · cele jakości usługi: [`docs/service-levels.md`](docs/service-levels.md)

## Technologie

<p align="center"><img src="docs/images/stack.png" alt="PostgreSQL, Python, Flask, Bash, PowerShell, Linux, Docker, Prometheus, Grafana, GPG, Azure, GitHub Actions" width="100%"></p>

## Co jest sprawdzone, a co nie

| Element | Stan |
|---|---|
| Baza, uprawnienia, audyt, widoki | Sprawdzone w całości (PostgreSQL 16) |
| ETL, kontrola dostaw, awarie na próbę, polecenie `guard` | Sprawdzone: 8 testów całego procesu na tymczasowej bazie oraz przebieg demo |
| Kopie zapasowe, test odtwarzania, kontrola stanu, maskowanie | Sprawdzone w całości |
| Konsola webowa | Sprawdzona: testy stron, uruchomienie samymi zmiennymi środowiskowymi (jak w kontenerze) |
| Skrypty PowerShell | Sprawdzone w PowerShell 7.4 na Linuksie. Windows PowerShell 5.1 i Windows Server: nietestowane |
| Docker Compose, Grafana, Prometheus | Plik zwalidowany (`docker compose config`, hadolint, `promtool`). Kontenerów nie uruchamiałem |
| GitHub Actions | Workflowy sprawdzone narzędziem `actionlint`. Pierwsze uruchomienie na GitHubie jeszcze przed nami |
| Azure, Pentaho | Opisane w `docs/`, nieuruchomione |

Znane ograniczenia: jeden serwer bez replikacji i odtwarzania do punktu w czasie, alarmy bez wysyłki e-mail/czat, małe dane demo.
Plan rozwoju: [`ROADMAP.md`](ROADMAP.md).

## Dokumentacja

Dokumentacja techniczna jest po angielsku (jak w większości zespołów IT):
[runbook](docs/runbook.md) · [ochrona danych / RODO](docs/data-protection.md) · [audyt „odziedziczonego” systemu](docs/legacy-audit.md) ·
[usprawnienie procesu: przed i po](docs/process-improvement.md) · [przykład zgłoszenia od użytkownika](docs/user-support-ticket.md) ·
[ćwiczenia awaryjne](docs/incidents/drills.md) · [jednostronicowe podsumowanie (PDF)](docs/guard-project-brief.pdf)

## O projekcie

Logo, film i wszystkie grafiki w tym repozytorium powstały w kodzie (Python + Skia), źródła: [`tools/video`](tools/video).
Kod: licencja [MIT](LICENSE) · [CONTRIBUTING](CONTRIBUTING.md) · [SECURITY](SECURITY.md) · [CHANGELOG](CHANGELOG.md) ·
[English README](README.en.md)
