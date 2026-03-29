from flask import Flask, request, render_template_string

app = Flask(__name__)

# -----------------------------
# RISK CALCULATION
# -----------------------------
def calculate_risk(data):
    score = 0
    reasons = []
    missing_tests = []

    age = int(data.get("age", 0))

    if age >= 45:
        score += 15
        reasons.append("Age above 45 increases diabetes risk.")

    if data.get("pcos") == "yes":
        score += 10
        reasons.append("PCOS is linked with insulin resistance.")

    if data.get("family") == "yes":
        score += 15
        reasons.append("Family history increases genetic risk.")

    if data.get("bp") == "yes":
        score += 10
        reasons.append("Hypertension contributes to metabolic risk.")

    if data.get("smoke") == "yes":
        score += 5
        reasons.append("Smoking affects insulin sensitivity.")

    # BMI
    bmi = float(data.get("bmi", 0) or 0)
    if bmi >= 30:
        score += 20
        reasons.append("Obesity (BMI ≥30) is a major risk factor.")
    elif bmi >= 25:
        score += 10
        reasons.append("Overweight increases diabetes risk.")

    # LABS
    if data.get("fbs"):
        if float(data["fbs"]) >= 126:
            score += 25
            reasons.append("High FBS suggests diabetes.")
    else:
        missing_tests.append("FBS")

    if data.get("hba1c"):
        if float(data["hba1c"]) >= 6.5:
            score += 25
            reasons.append("High HbA1c indicates poor glucose control.")
    else:
        missing_tests.append("HbA1c")

    if not data.get("rbs"):
        missing_tests.append("RBS")

    # LIFESTYLE
    if int(data.get("activity", 0) or 0) < 150:
        score += 10
        reasons.append("Physical activity <150 min/week increases risk.")

    if data.get("diet") == "yes":
        score += 10
        reasons.append("Frequent sugary food intake increases risk.")

    if data.get("sleep") == "yes":
        score += 5
        reasons.append("Poor sleep affects glucose metabolism.")

    # RISK LEVEL
    if score < 30:
        risk = "LOW"
        color = "green"
    elif score < 60:
        risk = "MODERATE"
        color = "yellow"
    else:
        risk = "HIGH"
        color = "red"

    return score, risk, color, reasons, missing_tests


# -----------------------------
# ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        score, risk, color, reasons, missing = calculate_risk(request.form)

        return render_template_string(RESULT_HTML,
                                      score=score,
                                      risk=risk,
                                      color=color,
                                      reasons=reasons,
                                      missing=missing)

    return render_template_string(FORM_HTML)


# -----------------------------
# FORM UI
# -----------------------------
FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Type 2 Diabetes Risk Predictor</title>

<style>
body {
    font-family: 'Segoe UI', sans-serif;
    margin:0;
    background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)),
    url("https://images.unsplash.com/photo-1580281657527-47f249e8f1e1") no-repeat center/cover;
    color:#333;
}

.container {
    max-width:500px;
    margin:30px auto;
    background:rgba(255,255,255,0.95);
    padding:20px;
    border-radius:12px;
}

h1 {
    text-align:center;
    color:#1565C0;
}

.step { display:none; }
.step.active { display:block; }

button {
    width:100%;
    padding:10px;
    margin-top:10px;
    background:#1565C0;
    color:white;
    border:none;
    border-radius:6px;
}

input, select {
    width:100%;
    padding:8px;
    margin-top:5px;
}

</style>

<script>
let step = 0;

function nextStep() {
    let steps = document.getElementsByClassName("step");
    steps[step].classList.remove("active");
    step++;
    steps[step].classList.add("active");
}

function showPCOS() {
    let gender = document.getElementById("gender").value;
    document.getElementById("pcosDiv").style.display =
        gender === "female" ? "block" : "none";
}

function toggleLabs() {
    let val = document.getElementById("labs").value;
    document.getElementById("labSection").style.display =
        val === "yes" ? "block" : "none";
}

// FIXED BMI CALCULATION
function calcBMI() {
    let w = parseFloat(document.getElementById("weight").value);
    let h = parseFloat(document.getElementById("height").value) / 100;

    if (w > 0 && h > 0) {
        let bmi = (w / (h*h)).toFixed(2);
        document.getElementById("bmi").value = bmi;
    } else {
        alert("Enter valid weight and height");
    }
}
</script>

</head>

<body>

<div class="container">

<h1>🩺 Type 2 Diabetes Risk Predictor</h1>
<h3 style="text-align:center;">Check Your Risk Here</h3>

<form method="POST">

<div class="step active">
Age:
<input type="number" name="age" required>

Gender:
<select name="gender" id="gender" onchange="showPCOS()">
<option value="male">Male</option>
<option value="female">Female</option>
</select>

<div id="pcosDiv" style="display:none;">
PCOS:
<select name="pcos">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>
</div>

<button type="button" onclick="nextStep()">Next</button>
</div>

<div class="step">
Have lab reports?
<select id="labs" onchange="toggleLabs()">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

<div id="labSection" style="display:none;">
FBS: <input name="fbs">
HbA1c: <input name="hba1c">
RBS: <input name="rbs">
</div>

<button type="button" onclick="nextStep()">Next</button>
</div>

<div class="step">
BMI:
<input id="bmi" name="bmi">

<p>Don't know BMI?</p>
Weight (kg): <input id="weight">
Height (cm): <input id="height">
<button type="button" onclick="calcBMI()">Calculate BMI</button>

<button type="button" onclick="nextStep()">Next</button>
</div>

<div class="step">
Activity (min/week):
<input name="activity">

Sugary foods?
<select name="diet">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

Sleep <6 hrs?
<select name="sleep">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

Smoking?
<select name="smoke">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

<button type="button" onclick="nextStep()">Next</button>
</div>

<div class="step">
Family history:
<select name="family">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

Hypertension:
<select name="bp">
<option value="no">No</option>
<option value="yes">Yes</option>
</select>

<button type="submit">Submit</button>
</div>

</form>
</div>

</body>
</html>
"""

# -----------------------------
# RESULT UI
# -----------------------------
RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body { font-family:Arial; background:#eef3f9; }

.card {
    max-width:500px;
    margin:30px auto;
    padding:20px;
    background:white;
    border-radius:10px;
}

.bar {
    height:20px;
    border-radius:10px;
    background:#ddd;
}

.fill {
    height:100%;
    border-radius:10px;
}

.green { background:green; }
.yellow { background:gold; }
.red { background:red; }

</style>
</head>

<body>

<div class="card">

<h2>Risk Level: <span style="color:{{color}}">{{risk}}</span></h2>

<div class="bar">
<div class="fill {{color}}" style="width:{{score}}%"></div>
</div>

<h3>Score: {{score}}</h3>

<h3>Reasons:</h3>
<ul>
{% for r in reasons %}
<li>{{r}}</li>
{% endfor %}
</ul>

{% if missing %}
<h3>⚠ Missing Tests:</h3>
<ul>
{% for m in missing %}
<li>Please perform {{m}}</li>
{% endfor %}
</ul>
{% endif %}

<h3>Recommendations:</h3>
<ul>
<li>Follow regular physical activity (150 min/week)</li>
<li>Eat fruits & vegetables daily</li>
<li>Maintain healthy weight</li>
<li>Consult doctor if risk is high</li>
</ul>

<button onclick="window.print()">Download Report</button>

<hr>

<p style="font-size:12px;">
THIS TOOL IS FOR EDUCATIONAL PURPOSE ONLY. CONSULT DOCTOR FOR DIAGNOSIS.<br>
DEVELOPED BY MANOJ KUMAR
</p>

</div>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)