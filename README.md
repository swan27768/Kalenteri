
# OpenDoors Bot

GitHub Actions -pohjainen kerääjä, joka hakee **avoimien ovien** (tai muiden tapahtumien) päivämäärät useista lähteistä, 
yhtenäistää ne ja **julkaisee automaattisesti GitHub Pagesiin** muodossa:

- `events.json`
- `opendoors.ics`

## Nopea aloitus

1. **Luo uusi repo** GitHubiin ja lataa tämä projekti sinne.
2. **Ota GitHub Pages käyttöön**: Settings → Pages → Build and deployment → Source: *GitHub Actions*.
3. (Valinnainen) Muokkaa `sources.yaml` ja lisää omat lähteesi.
4. Commitoa ja pushaa. Workflow pyörii **manuaalisesti** ja ajastettuna joka aamu.
5. Lopputulos löytyy osoitteesta `https://<user>.github.io/<repo>/events.json` ja `.../opendoors.ics`.

> Oletusajastus: joka päivä klo 07:00 (Europe/Helsinki). Muuta tiedosto `/.github/workflows/publish.yml`.

## Lähteiden määrittely

Muokkaa `sources.yaml`:
```yaml
ics:
  - name: IETF public calendar (esimerkki)
    url: https://www.ietf.org/calendar/ietf.ics
html:
  - name: Esimerkkisivu JSON-LD:llä
    url: https://example.org/events   # korvaa omalla sivulla
```

- **ICS**: suora iCal-linkki (julkinen).
- **HTML**: sivu, jossa on `application/ld+json` / `schema.org/Event`. Bot yrittää poimia sieltä tapahtumat.
  (Jos sivulla ei ole JSON-LD:tä, lisäät myöhemmin oman kerääjän `src/collectors/`-kansioon.)

## Kehitys paikallisesti

```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --out dist
```

Tulokset `dist/events.json` ja `dist/opendoors.ics`.

## Rakenne

```
src/
  collectors/
    ics.py         # iCal/ICS-lähteet
    jsonld.py      # HTML, jossa schema.org/Event JSON-LD
  model.py         # Event-malli ja iCal-kirjoitin
  main.py          # Orkestrointi
sources.yaml
.github/workflows/publish.yml
```

## Vastuullinen keräys

- Kunnioita `robots.txt` ja käyttöehtoja.
- Aseta selkeä User-Agent (`OpenDoorsBot/1.0 (+contact@example.com)`).
- Rate limit + välimuisti suositeltavaa (tässä minimiversiossa ei cachea).
- Lisää uusia kerääjiä lähdekohtaisesti (`src/collectors/*.py`).

## Lisenssi

MIT
