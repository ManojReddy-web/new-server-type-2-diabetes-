from flask import Flask, request, render_template_string

app = Flask(__name__)

# -----------------------------
# CONFIGURATION-DRIVEN SCORING
# -----------------------------
CONFIG = {
    "age_45": 15,
    "pcos": 10,
    "gestational": 12,
    "family": 15,
    "hypertension": 10,
    "smoking": 5,
    "obese_30": 20,
    "overweight_25": 10,
    "acanthosis": 18,
    "low_activity": 10,
    "diet_high_sugar": 10,
    "poor_sleep": 5,
    "lab_diabetic": 25,
    "lab_pre_diabetic": 10,
    "rbs_high": 15,
    "female_base": 5
}


def calculate_risk(data):
    score = 0
    reasons = []
    missing_tests = []

    # 1. Demographics & Gender Specifics
    try:
        age = int(data.get("age", 0) or 0)
        if age >= 45:
            score += CONFIG["age_45"]
            reasons.append("Age ≥ 45 is a primary non-modifiable risk factor.")
    except:
        pass

    gender = data.get("gender")
    if gender == "female":
        score += CONFIG["female_base"]
        if data.get("pcos") == "yes":
            score += CONFIG["pcos"]
            reasons.append("PCOS history indicates underlying insulin resistance.")
        if data.get("gestational") == "yes":
            score += CONFIG["gestational"]
            reasons.append("Previous Gestational Diabetes significantly increases Type 2 risk.")

    # 2. Clinical Signs (Acanthosis Nigricans)
    if data.get("acanthosis") == "yes":
        score += CONFIG["acanthosis"]
        reasons.append("Presence of Acanthosis Nigricans is a physical marker of high insulin levels.")

    # 3. Family & Comorbidities
    if data.get("family") == "yes":
        score += CONFIG["family"]
        reasons.append("First-degree family history suggests genetic predisposition.")
    if data.get("bp") == "yes":
        score += CONFIG["hypertension"]
        reasons.append("Hypertension is a component of Metabolic Syndrome.")

    # 4. BMI Calculation
    try:
        bmi = float(data.get("bmi", 0) or 0)
        if bmi >= 30:
            score += CONFIG["obese_30"]
            reasons.append(f"BMI of {bmi} (Obese) is a major contributor to insulin resistance.")
        elif bmi >= 25:
            score += CONFIG["overweight_25"]
            reasons.append(f"BMI of {bmi} (Overweight) increases metabolic load.")
    except:
        pass

    # 5. Lab Interpretation (Clinical Bands)
    lab_count = 0
    fbs_val = data.get("fbs")
    if fbs_val:
        try:
            val = float(fbs_val)
            lab_count += 1
            if val >= 126:
                score += CONFIG["lab_diabetic"]
                reasons.append(f"FBS ({val} mg/dL) is in the Diabetic range.")
            elif val >= 100:
                score += CONFIG["lab_pre_diabetic"]
                reasons.append(f"FBS ({val} mg/dL) is in the Pre-diabetic range.")
        except:
            pass
    else:
        missing_tests.append("Fasting Blood Sugar (FBS)")

    a1c_val = data.get("hba1c")
    if a1c_val:
        try:
            val = float(a1c_val)
            lab_count += 1
            if val >= 6.5:
                score += CONFIG["lab_diabetic"]
                reasons.append(f"HbA1c ({val}%) is in the Diabetic range.")
            elif val >= 5.7:
                score += CONFIG["lab_pre_diabetic"]
                reasons.append(f"HbA1c ({val}%) is in the Pre-diabetic range.")
        except:
            pass
    else:
        missing_tests.append("HbA1c (Glycated Hemoglobin)")

    # 6. Lifestyle
    if int(data.get("activity", 150) or 150) < 150:
        score += CONFIG["low_activity"]
        reasons.append("Physical activity below 150 min/week increases risk.")
    if data.get("diet") == "daily":
        score += CONFIG["diet_high_sugar"]
        reasons.append("Frequent sugary intake leads to glucose spikes.")
    if data.get("sleep") == "always":
        score += CONFIG["poor_sleep"]
        reasons.append("Chronic sleep deprivation disrupts glucose metabolism.")
    if data.get("smoke") == "yes":
        score += CONFIG["smoking"]
        reasons.append("Smoking increases oxidative stress and insulin resistance.")

    # 7. Final Normalization & Risk Banding
    final_score = min(score, 100)

    if final_score < 30:
        risk, color, emoji, action = "LOW", "#27ae60", "✅", "Low risk – Maintain healthy lifestyle and routine annual checkups."
    elif final_score < 65:
        risk, color, emoji, action = "MODERATE", "#f1c40f", "⚠️", "Moderate risk – Consider clinical lab tests and consult a GP for lifestyle modifications."
    else:
        risk, color, emoji, action = "HIGH", "#e74c3c", "🚨", "High risk – Early screening and referral to an Endocrinologist is strongly recommended."

    quality = "High" if lab_count == 2 else "Partial" if lab_count == 1 else "Low (No Labs)"

    return final_score, risk, color, reasons, missing_tests, emoji, action, quality


# -----------------------------
# UI TEMPLATES (Responsive & Mobile-Friendly)
# -----------------------------

FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diabetes Risk Predictor</title>
    <style>
        :root { --primary: #2980b9; --success: #27ae60; --dark: #2c3e50; }
        body { font-family: 'Segoe UI', sans-serif; margin:0; 
               background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
               url('https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=1350&q=80') center/cover fixed; 
               color:#fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { max-width:600px; width:92%; background:rgba(255,255,255,0.98); color:#333; padding:25px; border-radius:15px; box-shadow:0 10px 30px rgba(0,0,0,0.5); margin: 20px 0; }
        h1 { text-align:center; color:var(--primary); font-size: 1.8rem; margin-bottom: 5px; }
        .step { display:none; } .step.active { display:block; animation: fadeIn 0.4s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        label { font-weight:bold; display:block; margin-top:15px; font-size: 0.9rem; }
        input, select { width:100%; padding:12px; margin-top:5px; border:1px solid #ddd; border-radius:8px; box-sizing: border-box; font-size: 1rem; }
        .btn-group { margin-top:20px; display:flex; gap:10px; }
        button { flex:1; padding:14px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size: 1rem; transition: 0.3s; }
        .btn-next { background:var(--primary); color:white; }
        .btn-prev { background:#bdc3c7; color:#333; }
        .img-hint { width:100%; border-radius:10px; margin-top:10px; border: 1px solid #eee; }
        .info-box { font-size: 0.85rem; background:#ebf5fb; padding:12px; border-left:4px solid var(--primary); margin-top:10px; border-radius: 4px; }
    </style>
    <script>
        let step = 0;
        function nextStep() {
            let steps = document.getElementsByClassName("step");
            steps[step].classList.remove("active");
            step++;
            steps[step].classList.add("active");
            window.scrollTo(0,0);
        }
        function prevStep() {
            let steps = document.getElementsByClassName("step");
            steps[step].classList.remove("active");
            step--;
            steps[step].classList.add("active");
        }
        function showFemaleFields() {
            let gender = document.getElementById("gender").value;
            document.getElementById("femaleFields").style.display = gender === "female" ? "block" : "none";
        }
        function toggleLabs() {
            let val = document.getElementById("labs").value;
            document.getElementById("labSection").style.display = val === "yes" ? "block" : "none";
        }
        function calcBMI() {
            let w = parseFloat(document.getElementById("weight").value);
            let h = parseFloat(document.getElementById("height").value) / 100;
            if (w > 0 && h > 0) {
                document.getElementById("bmi").value = (w / (h*h)).toFixed(2);
            }
        }
    </script>
</head>
<body>
<div class="container">
    <h1>🩺 Risk Predictor V2.0</h1>
    <p style="text-align:center; font-size:0.8rem; margin-top:0;">Clinical Grade Screening Tool</p>
    <form method="POST">
        <div class="step active">
            <label>Full Age</label><input type="number" name="age" required placeholder="e.g. 45">
            <label>Biological Gender</label>
            <select name="gender" id="gender" onchange="showFemaleFields()">
                <option value="male">Male</option><option value="female">Female</option>
            </select>
            <div id="femaleFields" style="display:none;">
                <label>PCOS Diagnosis?</label><select name="pcos"><option value="no">No</option><option value="yes">Yes</option></select>
                <label>History of Gestational Diabetes?</label><select name="gestational"><option value="no">No</option><option value="yes">Yes</option></select>
            </div>
            <div class="btn-group"><button type="button" class="btn-next" onclick="nextStep()">Continue</button></div>
        </div>

        <div class="step">
            <label>Acanthosis Nigricans Check</label>
            <p style="font-size:0.85rem; color:#666;">Do you have dark, velvety skin patches in folds like your neck or armpits?</p>
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Acanthosis_nigricans_2.jpg/300px-Acanthosis_nigricans_2.jpg" class="img-hint" alt="Acanthosis Nigricans">
            <select name="acanthosis"><option value="no">No</option><option value="yes">Yes</option></select>
            <div class="info-box">This is a sign of <strong>Insulin Resistance</strong> where the body makes extra insulin to manage blood sugar.</div>
            <div class="btn-group">
                <button type="button" class="btn-prev" onclick="prevStep()">Back</button>
                <button type="button" class="btn-next" onclick="nextStep()">Continue</button>
            </div>
        </div>

        <div class="step">
            <label>Body Mass Index (BMI)</label>
            <input id="bmi" name="bmi" placeholder="BMI Value">
            <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-top:10px; border: 1px dashed #ccc;">
                <small>Quick Calculate:</small><br>
                <input id="weight" placeholder="Weight (kg)" style="width:48%;"> <input id="height" placeholder="Height (cm)" style="width:48%;">
                <button type="button" onclick="calcBMI()" style="background:#7f8c8d; color:white; width:100%; margin-top:5px; padding:8px;">Calculate</button>
            </div>
            <label>Laboratory Reports?</label>
            <select id="labs" onchange="toggleLabs()"><option value="no">No</option><option value="yes">Yes</option></select>
            <div id="labSection" style="display:none;">
                <label>FBS (mg/dL)</label><input name="fbs">
                <label>HbA1c (%)</label><input name="hba1c">
                <label>RBS (mg/dL)</label><input name="rbs">
            </div>
            <div class="btn-group">
                <button type="button" class="btn-prev" onclick="prevStep()">Back</button>
                <button type="button" class="btn-next" onclick="nextStep()">Continue</button>
            </div>
        </div>

        <div class="step">
            <label>Lifestyle Factors</label>
            <label>Physical Activity (min/week)</label><input type="number" name="activity" placeholder="e.g. 150">
            <label>Frequent Sugary/Processed Foods?</label>
            <select name="diet"><option value="no">Rarely</option><option value="daily">Daily</option></select>
            <label>Sleep < 6 hours daily?</label>
            <select name="sleep"><option value="no">No</option><option value="always">Yes</option></select>
            <label>Smoking Status</label>
            <select name="smoke"><option value="no">Non-smoker</option><option value="yes">Smoker</option></select>
            <div class="btn-group">
                <button type="button" class="btn-prev" onclick="prevStep()">Back</button>
                <button type="button" class="btn-next" onclick="nextStep()">Next</button>
            </div>
        </div>

        <div class="step">
            <label>Medical History</label>
            <label>Family History (Parents/Siblings)?</label>
            <select name="family"><option value="no">No</option><option value="yes">Yes</option></select>
            <label>Hypertension (High BP)?</label>
            <select name="bp"><option value="no">No</option><option value="yes">Yes</option></select>
            <div class="btn-group">
                <button type="button" class="btn-prev" onclick="prevStep()">Back</button>
                <button type="submit" style="background:var(--success); color:white;">Generate Final Report</button>
            </div>
        </div>
    </form>
</div>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Risk Assessment Report</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background:#f4f7f6; margin:0; padding:15px; color: #333; }
        .report-card { max-width:800px; margin:auto; background:white; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); }
        .header { border-bottom: 3px solid #2980b9; padding-bottom:15px; margin-bottom:20px; display:flex; justify-content:space-between; align-items: center; }

        /* Speedometer Styles */
        .gauge-container { width: 180px; height: 90px; position: relative; margin: 20px auto; overflow: hidden; }
        .gauge-bg { width: 180px; height: 180px; border-radius: 50%; border: 18px solid #eee; box-sizing: border-box; }
        .gauge-color { width: 180px; height: 180px; border-radius: 50%; border: 18px solid {{color}}; box-sizing: border-box;
                       position: absolute; top:0; left:0; clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%);
                       transform: rotate({{ (score * 1.8) - 90 }}deg); transition: transform 1.5s cubic-bezier(0.17, 0.67, 0.83, 0.67); }
        .gauge-text { text-align:center; font-size:2rem; font-weight:bold; margin-top:-35px; position:relative; z-index:10; }

        .food-table { width:100%; border-collapse: collapse; margin-top:20px; font-size: 0.85rem; line-height: 1.4; }
        .food-table th, .food-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .food-table th { background: #f8f9fa; color: #2c3e50; }
        .status-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 5px; }

        .pro-tip { background: #e8f8f5; border-left: 5px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .disclaimer { font-size: 0.75rem; color: #7f8c8d; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-style: italic; }

        @media (max-width: 600px) {
            .header { flex-direction: column; text-align: center; }
            .food-table { font-size: 0.75rem; }
            .gauge-container { width: 140px; height: 70px; }
            .gauge-bg, .gauge-color { width: 140px; height: 140px; }
            .gauge-text { font-size: 1.5rem; margin-top: -25px; }
        }
        @media print { .no-print { display:none; } body { background:white; } .report-card { box-shadow:none; padding:0; } }
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div><strong style="font-size: 1.2rem; color: #2980b9;">Clinical Screening Report</strong><br><small>Generated: 2026-03-28</small></div>
            <div style="font-size: 0.8rem; border: 1px solid #ddd; padding: 5px 10px; border-radius: 5px;">Quality: <strong>{{quality}}</strong></div>
        </div>

        <div style="text-align:center;">
            <div class="gauge-container"><div class="gauge-bg"></div><div class="gauge-color"></div></div>
            <div class="gauge-text">{{score}}%</div>
            <h2 style="margin: 10px 0 5px; color:{{color}}">{{emoji}} {{risk}} RISK</h2>
            <p style="font-size: 0.95rem; font-weight: 500;">{{action}}</p>
        </div>

        <hr style="border:0; border-top:1px solid #eee;">
        <h3>Identified Risk Indicators:</h3>
        <ul style="font-size:0.9rem; padding-left: 20px;">
            {% for r in reasons %}<li>{{r}}</li>{% endfor %}
        </ul>

        {% if missing %}
        <div style="background:#fff3cd; padding:15px; border-radius:8px; margin-top:15px; border-left: 5px solid #f1c40f;">
            <strong>⚠️ Caution:</strong> To improve accuracy, consider these lab tests: <strong>{{ missing|join(', ') }}</strong>.
        </div>
        {% endif %}

        <hr style="border:0; border-top:1px solid #eee;">
        <h3>🥗 Nutritional Guidance (Indian Context)</h3>
        <p style="font-size:0.85rem; margin-bottom:15px;">Managing glucose depends heavily on <strong>portion control</strong> and <strong>food frequency</strong>.</p>

        <table class="food-table">
            <thead>
                <tr>
                    <th style="width: 33%;"><span class="status-dot" style="background:#e74c3c;"></span>🔴 High Spike</th>
                    <th style="width: 33%;"><span class="status-dot" style="background:#f1c40f;"></span>🟡 Moderate</th>
                    <th style="width: 33%;"><span class="status-dot" style="background:#27ae60;"></span>🟢 Safe / Low</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>White Rice, Maida, Naan, Pizza, White Bread, Pasta, Instant Noodles</td>
                    <td>Brown Rice, Whole Wheat Roti, Semolina (Upma), Basmati Rice</td>
                    <td>Millets (Jowar, Bajra, Ragi), Oats, Quinoa, Broken Wheat (Dalia)</td>
                </tr>
                <tr>
                    <td>Sweets (Laddu, Jalebi), Cakes, Soda, Packaged Juices</td>
                    <td>Papaya, Watermelon, Pineapple</td>
                    <td>Apple (with skin), Guava, Jamun, Berries, Citrus Fruits</td>
                </tr>
                <tr>
                    <td>Mango, Chikoo, Grapes, Ripe Banana, Potato, Corn</td>
                    <td>Sweet Potato, Beetroot</td>
                    <td>Leafy Greens, Cucumber, Broccoli, Sprouts, Nuts, Seeds</td>
                </tr>
            </tbody>
        </table>

        <div class="pro-tip">
            <strong>💡 Pro-Tip: "Food Sequencing"</strong><br>
            Eat your <strong>Fiber (Salads)</strong> first, followed by <strong>Protein (Dal/Paneer/Eggs)</strong>, and <strong>Carbs (Roti/Rice)</strong> last. This significantly flattens the sugar spike after meals.
        </div>

        <div class="no-print" style="margin-top:30px; display: flex; gap: 10px;">
            <button onclick="window.print()" style="background:#2c3e50; color:white; flex: 2;">Download Report (PDF)</button>
            <button onclick="window.location.href='/'" style="background:#eee; color:#333; flex: 1;">New Check</button>
        </div>

        <div class="disclaimer">
            The information provided is based on clinical risk factors and is not a medical diagnosis. High sugar foods cause rapid spikes because they are quickly digested. Portion control is key even for "Safe" foods.
        </div>
    </div>
</body>
</html>
"""


# -----------------------------
# MAIN APP ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        score, risk, color, reasons, missing, emoji, action, quality = calculate_risk(request.form)
        return render_template_string(RESULT_HTML, score=score, risk=risk, color=color,
                                      reasons=reasons, missing=missing, emoji=emoji,
                                      action=action, quality=quality)
    return render_template_string(FORM_HTML)


if __name__ == "__main__":
    app.run(debug=True)app
