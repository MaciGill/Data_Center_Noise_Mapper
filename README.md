# Data Center Noise Mapper
This project was created in response to the development of new data centers near Polish cities.
One such city is Bielsko-Biała, where construction of a data center at the former FIAT facilities is being considered.
I wanted to explore the potential impact of such a building on local residents.
Using data available from other data centers, including those in the United Kingdom, I created a simplified model that represents the impact area as concentric circles.
This is a highly simplified model that does not account for many factors, such as sound propagation or terrain-related limitations.
The project generates an interactive map of illustrative noise zones around a selected source. You can move the marker and switch between profiles; the HTML map is saved in the `output/` directory.

## Running the project

Python 3 is required. From the project directory, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\main.py
```

Map profiles are defined in `data/noise_profiles.json`. The example radii are illustrative and are not a calibrated noise forecast.
