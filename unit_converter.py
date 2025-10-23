# -*- coding: utf-8 -*-
# Semplice convertitore di unità con Flask in un singolo file.
# UI minimale con Bootstrap; tutte le conversioni avvengono lato server.

from flask import Flask, request, render_template_string, redirect, url_for, flash
from math import pi, isclose
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# -------------------------------
# Modello dati: unità e fattori
# -------------------------------

class Affine:
    def __init__(self, to_base, from_base):
        self.to_base = to_base
        self.from_base = from_base

UNITS = {
    # Lunghezza — base: metro
    "length": {
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "mi": 1609.344,
        "yd": 0.9144,
        "ft": 0.3048,
        "in": 0.0254,
    },
    # Volume — base: litro
    "volume": {
        "L": 1.0,
        "mL": 0.001,
        "m³": 1000.0,      # metro cubo in litri
        "gal_US": 3.785411784,
        "qt_US": 0.946352946,
        "pt_US": 0.473176473,
        "cup_US": 0.2365882365,
        "fl_oz_US": 0.02957352956,
    },
    # Massa — base: chilogrammo
    "mass": {
        "kg": 1.0,
        "g": 0.001,
        "mg": 1e-6,
        "lb": 0.45359237,
        "oz": 0.028349523125,
        "t": 1000.0,
    },
    # Area — base: metro quadrato
    "area": {
        "m²": 1.0,
        "km²": 1_000_000.0,
        "cm²": 0.0001,
        "mm²": 1e-6,
        "ha": 10_000.0,
        "ac": 4046.8564224,
        "ft²": 0.09290304,
        "yd²": 0.83612736,
        "in²": 0.00064516,
    },
    # Velocità — base: m/s
    "speed": {
        "m/s": 1.0,
        "km/h": 1000.0/3600.0,
        "mph": 1609.344/3600.0,
        "kn": 1852.0/3600.0,
    },
    # Tempo — base: secondo
    "time": {
        "s": 1.0,
        "ms": 0.001,
        "min": 60.0,
        "h": 3600.0,
        "day": 86400.0,
    },
    # Dati — base: byte
    "data": {
        "B": 1.0,
        "KB": 1024.0,
        "MB": 1024.0**2,
        "GB": 1024.0**3,
        "TB": 1024.0**4,
        "kbit": 1000.0/8.0,
        "Mbit": 1_000_000.0/8.0,
        "Gbit": 1_000_000_000.0/8.0,
    },
    # Pressione — base: pascal
    "pressure": {
        "Pa": 1.0,
        "kPa": 1000.0,
        "bar": 100_000.0,
        "mbar": 100.0,
        "psi": 6894.757293168,
        "atm": 101_325.0,
        "mmHg": 133.3223684211,
    },
    # Temperatura — base: kelvin (affine)
    "temperature": {
        "K": Affine(lambda x: x, lambda k: k),
        "°C": Affine(lambda c: c + 273.15, lambda k: k - 273.15),
        "°F": Affine(lambda f: (f - 32.0) * 5.0/9.0 + 273.15,
                     lambda k: (k - 273.15) * 9.0/5.0 + 32.0),
        "°R": Affine(lambda r: r * 5.0/9.0, lambda k: k * 9.0/5.0),
    },
    # Angolo — base: radiante
    "angle": {
        "rad": 1.0,
        "deg": pi/180.0,
        "grad": pi/200.0,
        "turn": 2*pi,
    },
}

DIMENSION_LABELS = {
    "length": "Lunghezza",
    "volume": "Volume",
    "mass": "Massa",
    "area": "Area",
    "speed": "Velocità",
    "time": "Tempo",
    "data": "Dati",
    "pressure": "Pressione",
    "temperature": "Temperatura",
    "angle": "Angolo",
}

# -------------------------------
# Utility
# -------------------------------

def _is_affine(unit_def):
    return isinstance(unit_def, Affine)


def _to_base(dim, value, unit):
    u = UNITS[dim][unit]
    return u.to_base(value) if _is_affine(u) else value * u


def _from_base(dim, base_value, unit):
    u = UNITS[dim][unit]
    return u.from_base(base_value) if _is_affine(u) else base_value / u


def convert(dim, value, unit_from, unit_to):
    if unit_from == unit_to:
        return value
    return _from_base(dim, _to_base(dim, value, unit_from), unit_to)


def _sorted_units_map():
    return {d: sorted(UNITS[d].keys()) for d in UNITS}


def _dimensions_list():
    return [(k, DIMENSION_LABELS.get(k, k.title())) for k in UNITS.keys()]


def _fmt(x: float) -> str:
    s = f"{x:.12f}"
    return s.rstrip('0').rstrip('.')

# -------------------------------
# HTML
# -------------------------------

TEMPLATE = """
<!doctype html>
<html lang=\"it\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Converti Unità</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
      :root{--bg:#0b0f18;--panel:#121826;--muted:#b6c2cf;--text:#f2f5f9;--input:#0e1420;--border:#2a3a55}
      body{background:var(--bg);color:var(--text)}
      .navbar{background:#0f172a}
      .card{background:var(--panel);border:1px solid var(--border)}
      .card-header{border-bottom:1px solid var(--border);color:var(--text)}
      .form-label{color:var(--text)}
      .form-control,.form-select{background:var(--input);border:1px solid var(--border);color:var(--text)}
      .form-control::placeholder{color:#9fb0c4;opacity:1}
      .form-select:focus,.form-control:focus{border-color:#60a5fa;box-shadow:none}
      .btn-primary{background:#2563eb;border-color:#2563eb}
      .btn-outline-light{color:var(--text);border-color:#94a3b8}
      .unit-chip{background:var(--input);border:1px solid var(--border);border-radius:999px;padding:.25rem .6rem;margin:.15rem;display:inline-block;color:var(--text)}
      .muted{color:var(--muted)}
    </style>
  </head>
  <body>
    <nav class=\"navbar navbar-dark mb-4\">
      <div class=\"container\">
        <span class=\"navbar-brand mb-0 h1\">Converti Unità</span>
      </div>
    </nav>

    <div class=\"container\" style=\"max-width: 980px;\">
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class=\"alert alert-warning\">{{ messages[0] }}</div>
        {% endif %}
      {% endwith %}

      <div class=\"card mb-4\">
        <div class=\"card-header\">Conversione</div>
        <div class=\"card-body\">
          <form method=\"post\" action=\"{{ url_for('convert_route') }}\" class=\"row g-3 align-items-end\">
            <div class=\"col-md-4\">
              <label class=\"form-label\">Categoria</label>
              <select name=\"dimension\" class=\"form-select\" id=\"dimension\" required>
                {% for key, label in dimensions %}
                  <option value=\"{{ key }}\" {% if key == current_dim %}selected{% endif %}>{{ label }}</option>
                {% endfor %}
              </select>
            </div>

            <div class=\"col-md-4\">
              <label class=\"form-label\">Valore</label>
              <input type=\"number\" step=\"any\" name=\"value\" class=\"form-control\" placeholder=\"Es: 25\" required value=\"{{ value or '' }}\">
            </div>

            <div class=\"col-md-4 d-grid d-md-block\">
              <button class=\"btn btn-primary w-100\">Calcola</button>
            </div>

            <div class=\"col-md-6\">
              <label class=\"form-label\">Da</label>
              <select name=\"unit_from\" class=\"form-select\" id=\"unit_from\" required>
                {% for u in units %}
                  <option value=\"{{ u }}\" {% if u == unit_from %}selected{% endif %}>{{ u }}</option>
                {% endfor %}
              </select>
            </div>
            <div class=\"col-md-6\">
              <label class=\"form-label\">A</label>
              <select name=\"unit_to\" class=\"form-select\" id=\"unit_to\" required>
                {% for u in units %}
                  <option value=\"{{ u }}\" {% if u == unit_to %}selected{% endif %}>{{ u }}</option>
                {% endfor %}
              </select>
            </div>
          </form>

          {% if result is not none %}
            <hr/>
            <div class=\"d-flex align-items-center justify-content-between\">
              <div>
                <div class=\"h5 mb-0\">Risultato</div>
                <div class=\"muted\">{{ value }} {{ unit_from }} = <strong>{{ formatted_result }}</strong> {{ unit_to }}</div>
              </div>
              <form method=\"post\" action=\"{{ url_for('swap_route') }}\">
                <input type=\"hidden\" name=\"dimension\" value=\"{{ current_dim }}\"/>
                <input type=\"hidden\" name=\"value\" value=\"{{ result }}\"/>
                <input type=\"hidden\" name=\"unit_from\" value=\"{{ unit_to }}\"/>
                <input type=\"hidden\" name=\"unit_to\" value=\"{{ unit_from }}\"/>
                <button class=\"btn btn-outline-light\">Inverti</button>
              </form>
            </div>
          {% endif %}
        </div>
      </div>

      <div class=\"card\">
        <div class=\"card-header\">Unità disponibili</div>
        <div class=\"card-body row\">
          {% for key, label in dimensions %}
            <div class=\"col-md-6 mb-3\">
              <div class=\"fw-semibold\">{{ label }}</div>
              <div class=\"mt-1\">
                {% for u in all_units[key] %}
                  <span class=\"unit-chip\">{{ u }}</span>
                {% endfor %}
              </div>
            </div>
          {% endfor %}
        </div>
      </div>

      <p class=\"mt-4 muted\">Esempi: °C ↔ °F ↔ K · L ↔ gal_US · m ↔ yd · deg ↔ grad ↔ rad.</p>
    </div>

    <script>
      const unitMap = {{ all_units|tojson }};
      const dimSel = document.getElementById('dimension');
      const fromSel = document.getElementById('unit_from');
      const toSel = document.getElementById('unit_to');
      function repopulate(){
        const units = unitMap[dimSel.value];
        fromSel.innerHTML = units.map(u=>`<option value=\"${u}\">${u}</option>`).join('');
        toSel.innerHTML = units.map(u=>`<option value=\"${u}\">${u}</option>`).join('');
      }
      if(dimSel){ dimSel.addEventListener('change', repopulate); }
    </script>
  </body>
</html>
"""

# -------------------------------
# Route
# -------------------------------

@app.route("/", methods=["GET"])
def index():
    default_dim = "temperature"
    units = _sorted_units_map()
    return render_template_string(
        TEMPLATE,
        dimensions=_dimensions_list(),
        all_units=units,
        units=units[default_dim],
        current_dim=default_dim,
        value=None,
        unit_from=units[default_dim][0],
        unit_to=units[default_dim][1],
        result=None,
        formatted_result=None,
    )


@app.route("/convert", methods=["POST"])
def convert_route():
    try:
        dim = request.form.get("dimension")
        if dim not in UNITS:
            flash("Categoria non valida.")
            return redirect(url_for("index"))
        value = float(request.form.get("value", ""))
        unit_from = request.form.get("unit_from")
        unit_to = request.form.get("unit_to")
        if unit_from not in UNITS[dim] or unit_to not in UNITS[dim]:
            flash("Unità non valide per la categoria selezionata.")
            return redirect(url_for("index"))
        result = convert(dim, value, unit_from, unit_to)
        units = _sorted_units_map()
        return render_template_string(
            TEMPLATE,
            dimensions=_dimensions_list(),
            all_units=units,
            units=units[dim],
            current_dim=dim,
            value=value,
            unit_from=unit_from,
            unit_to=unit_to,
            result=result,
            formatted_result=_fmt(result),
        )
    except ValueError:
        flash("Inserisci un numero valido.")
        return redirect(url_for("index"))


@app.route("/swap", methods=["POST"])
def swap_route():
    dim = request.form.get("dimension")
    try:
        value = float(request.form.get("value"))
    except (TypeError, ValueError):
        return redirect(url_for("index"))
    unit_from = request.form.get("unit_from")
    unit_to = request.form.get("unit_to")
    units = _sorted_units_map()
    return render_template_string(
        TEMPLATE,
        dimensions=_dimensions_list(),
        all_units=units,
        units=units.get(dim, units["temperature"]),
        current_dim=dim,
        value=value,
        unit_from=unit_from,
        unit_to=unit_to,
        result=None,
        formatted_result=None,
    )

# -------------------------------
# Self-test opzionale (silenzioso)
# -------------------------------

def _selftest():
    if os.environ.get("RUN_TESTS") != "1":
        return
    def check(name, a, b, tol=1e-9):
        if not isclose(a, b, rel_tol=tol, abs_tol=tol):
            print(f"[TEST] {name}: KO (got {a}, expected {b})")
    check("0°C -> 32°F", convert("temperature", 0, "°C", "°F"), 32.0)
    check("100°C -> 373.15K", convert("temperature", 100, "°C", "K"), 373.15)
    check("1 L -> gal_US", convert("volume", 1, "L", "gal_US"), 1/3.785411784)
    check("180 deg -> rad", convert("angle", 180, "deg", "rad"), pi)

# -------------------------------
# Avvio semplice
# -------------------------------

if __name__ == "__main__":
    _selftest()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=False)
