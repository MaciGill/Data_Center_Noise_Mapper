# Data Center Noise Mapper

Projekt generuje interaktywną mapę przykładowych stref hałasu wokół wskazanego źródła. Można przesuwać znacznik oraz przełączać profile; mapa HTML jest zapisywana w katalogu `output/`.

## Uruchomienie

Wymagany jest Python 3. Z katalogu projektu wykonaj:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\main.py
```

Profile mapy są w `data/noise_profiles.json`. Przykładowe promienie są poglądowe i nie stanowią skalibrowanej prognozy hałasu.
