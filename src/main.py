import json
from pathlib import Path

import folium
from branca.element import MacroElement
from jinja2 import Template


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "noise_profiles.json"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "bielsko_biala_noise_map.html"

OUTPUT_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# 2. Load profiles
# --------------------------------------------------

with open(DATA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

profiles = data["profiles"]

if not profiles:
    raise ValueError("No noise profiles found in the JSON file.")

profile_ids = [profile["id"] for profile in profiles]

if len(profile_ids) != len(set(profile_ids)):
    raise ValueError("Profile IDs must be unique.")

for profile in profiles:
    if not profile.get("levels"):
        raise ValueError(
            f"Profile {profile['id']} contains no noise levels."
        )


# --------------------------------------------------
# 3. Map settings
# --------------------------------------------------

START_LAT = 49.8225
START_LON = 19.0444

ACTIVE_PROFILE_ID = profiles[0]["id"]

noise_map = folium.Map(
    location=[START_LAT, START_LON],
    zoom_start=12,
    tiles="OpenStreetMap"
)


# --------------------------------------------------
# 4. Noise source marker
# --------------------------------------------------

marker = folium.Marker(
    location=[START_LAT, START_LON],
    tooltip="Drag to move the noise source",
    popup="Noise source",
    draggable=True,
    icon=folium.Icon(
        color="red",
        icon="volume-up",
        prefix="fa"
    )
)

marker.add_to(noise_map)


# --------------------------------------------------
# 5. Create zones for all profiles
# --------------------------------------------------

circle_objects = {}

for profile in profiles:

    profile_id = profile["id"]
    circle_objects[profile_id] = []

    is_active = profile_id == ACTIVE_PROFILE_ID

    for level in profile["levels"]:

        circle = folium.Circle(
            location=[START_LAT, START_LON],
            radius=level["radius_m"],
            color=level["color"],
            weight=2,
            fill=True,
            fill_color=level["color"],
            fill_opacity=0.16 if is_active else 0,
            opacity=0.85 if is_active else 0,
            tooltip=f"{level['db']} dB(A)"
        )

        circle.add_to(noise_map)

        circle_objects[profile_id].append(circle)


# --------------------------------------------------
# 6. Profile selection and information panel
# --------------------------------------------------

profile_data = []

for profile in profiles:
    profile_data.append({
        "id": profile["id"],
        "name": profile["name"],
        "source": profile.get("source", ""),
        "description": profile.get("description", ""),
        "levels": profile["levels"]
    })


class NoiseProfileControl(MacroElement):

    def __init__(self, marker, circle_objects, profiles, active_id):

        super().__init__()

        self._name = "NoiseProfileControl"

        self.marker_name = marker.get_name()

        self.circle_names = {
            profile_id: [
                circle.get_name()
                for circle in circles
            ]
            for profile_id, circles in circle_objects.items()
        }

        self.profiles = profiles
        self.active_id = active_id

        self._template = Template("""
        {% macro script(this, kwargs) %}

        var marker = {{ this.marker_name }};
        var circleNames = {{ this.circle_names | tojson }};
        var profiles = {{ this.profiles | tojson }};
        var activeProfileId = {{ this.active_id | tojson }};

        var circles = {};

        // References to all circles
        Object.keys(circleNames).forEach(function(profileId) {

            circles[profileId] = circleNames[profileId].map(
                function(circleName) {
                    return window[circleName];
                }
            );

        });

        // Control panel
        var control = L.control({position: "topright"});

        control.onAdd = function(map) {

            var div = L.DomUtil.create(
                "div",
                "noise-profile-control"
            );

            div.style.background = "white";
            div.style.padding = "12px";
            div.style.borderRadius = "8px";
            div.style.boxShadow = "0 1px 6px rgba(0,0,0,0.3)";
            div.style.width = "260px";
            div.style.fontSize = "13px";

            var options = profiles.map(function(profile) {
                return '<option value="' + profile.id + '">' +
                    profile.name +
                    '</option>';
            }).join("");

            div.innerHTML = `
                <div style="font-weight:bold; margin-bottom:8px;">
                    Data center noise profile
                </div>

                <select id="profileSelector"
                    style="width:100%; padding:6px; margin-bottom:10px;">
                    ${options}
                </select>

                <div id="profileDescription"
                    style="margin-bottom:8px;"></div>

                <div id="profileSource"
                    style="font-size:11px; color:#666;"></div>

                <hr>

                <div style="font-weight:bold;">
                    Source location
                </div>

                <div id="coordinates"
                    style="margin-top:5px;"></div>
            `;

            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);

            return div;
        };

        control.addTo({{ this._parent.get_name() }});

        // Update zone visibility
        function updateProfile(profileId) {

            activeProfileId = profileId;

            profiles.forEach(function(profile) {

                var isActive = profile.id === profileId;

                circles[profile.id].forEach(function(circle) {

                    circle.setStyle({
                        opacity: isActive ? 0.85 : 0,
                        fillOpacity: isActive ? 0.16 : 0
                    });

                });

            });

            var selected = profiles.find(function(profile) {
                return profile.id === profileId;
            });

            document.getElementById(
                "profileDescription"
            ).textContent = selected.description || "";

            document.getElementById(
                "profileSource"
            ).textContent = "Source: " + selected.source;

        }

        // Move all profiles with the marker
        function updatePosition(position) {

            Object.keys(circles).forEach(function(profileId) {

                circles[profileId].forEach(function(circle) {
                    circle.setLatLng(position);
                });

            });

            document.getElementById(
                "coordinates"
            ).textContent =
                position.lat.toFixed(6) + ", " +
                position.lng.toFixed(6);

        }

        marker.on("drag", function(event) {
            updatePosition(event.target.getLatLng());
        });

        marker.on("dragend", function(event) {
            updatePosition(event.target.getLatLng());
        });

        document.getElementById(
            "profileSelector"
        ).addEventListener("change", function(event) {
            updateProfile(event.target.value);
        });

        // Initialization
        document.getElementById(
            "profileSelector"
        ).value = activeProfileId;

        updateProfile(activeProfileId);
        updatePosition(marker.getLatLng());

        {% endmacro %}
        """)


# --------------------------------------------------
# 7. Add the control to the map
# --------------------------------------------------

control = NoiseProfileControl(
    marker=marker,
    circle_objects=circle_objects,
    profiles=profile_data,
    active_id=ACTIVE_PROFILE_ID
)

noise_map.add_child(control)


# --------------------------------------------------
# 8. Legend
# --------------------------------------------------

legend = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
z-index: 9999;
background: white;
padding: 12px;
border-radius: 8px;
box-shadow: 0 1px 6px rgba(0,0,0,0.3);
font-size: 12px;
">
<b>Noise levels</b><br>
<span style="color:#8B0000;">●</span> 65 dB(A)<br>
<span style="color:#E53935;">●</span> 60 dB(A)<br>
<span style="color:#FB8C00;">●</span> 55 dB(A)<br>
<span style="color:#FDD835;">●</span> 50 dB(A)<br>
<span style="color:#7CB342;">●</span> 45 dB(A)<br>
<span style="color:#26A69A;">●</span> 40 dB(A)<br>
<span style="color:#42A5F5;">●</span> 35 dB(A)
</div>
"""

noise_map.get_root().html.add_child(
    folium.Element(legend)
)


# --------------------------------------------------
# 9. Save the map
# --------------------------------------------------

noise_map.save(OUTPUT_FILE)

print(f"Map saved to: {OUTPUT_FILE}")