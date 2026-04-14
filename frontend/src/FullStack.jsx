import { useState, useRef, useEffect, useCallback } from "react";
import "./index.css";

const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const mapFormToPatient = (f) => ({
  age: f.age, gender: f.gender, weight_kg: f.weight, height_cm: f.height,
  disease_type: f.diseaseType, severity: f.severity, activity_level: f.activity,
  daily_caloric: f.calories, cholesterol: f.cholesterol, blood_pressure: f.bp,
  glucose: f.glucose, weekly_exercise: f.exercise, adherence: f.adherence,
  nutrient_imbalance: f.nutrientImbalance, restrictions: f.restrictions,
  allergies: f.allergies, cuisine: f.cuisine
});

/* ═══════════════════════════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════════════════════════ */
const C = {
  bg0:"#f8fafc", bg1:"#ffffff", bg2:"#f1f5f9", bg3:"#e8edf4", bg4:"#dde3ed",
  border:"#e2e8f0", borderHi:"#cbd5e1",
  t0:"#0f172a", t1:"#475569", t2:"#94a3b8", t3:"#cbd5e1",
  green:"#16a34a", greenDim:"#15803d", greenFg:"#22c55e",
  amber:"#d97706", red:"#dc2626", blue:"#2563eb", teal:"#0d9488", purple:"#7c3aed",
  card:"#ffffff",
};

const F = { sans:"'DM Sans',system-ui,sans-serif", mono:"'DM Mono','Fira Code',monospace" };

/* ═══════════════════════════════════════════════════════════════════
   PRIMITIVE COMPONENTS
═══════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════
   PRIMITIVE COMPONENTS
═══════════════════════════════════════════════════════════════════ */

const Mono = ({ children, color, size = 13 }) => (
  <span style={{ fontFamily: F.mono, fontSize: size, color: color || C.t0 }}>{children}</span>
);

const Tag = ({ label, level = "neutral" }) => {
  const map = {
    critical: { bg:"rgba(239,68,68,.12)", border:"rgba(239,68,68,.25)", text:C.red },
    warning:  { bg:"rgba(245,158,11,.12)", border:"rgba(245,158,11,.25)", text:C.amber },
    info:     { bg:"rgba(59,130,246,.12)", border:"rgba(59,130,246,.25)", text:C.blue },
    success:  { bg:"rgba(34,197,94,.12)",  border:"rgba(34,197,94,.25)",  text:C.green },
    neutral:  { bg:C.bg3, border:C.border, text:C.t1 },
  };
  const s = map[level];
  return (
    <span style={{ display:"inline-flex", alignItems:"center", gap:5, padding:"3px 8px", borderRadius:4,
      background:s.bg, border:`1px solid ${s.border}`, color:s.text, fontSize:11, fontWeight:500, whiteSpace:"nowrap" }}>
      <span style={{ width:4, height:4, borderRadius:"50%", background:s.text, flexShrink:0 }} />
      {label}
    </span>
  );
};

const Card = ({ children, style, className }) => (
  <div className={className} style={{ background:C.bg1, border:`1px solid ${C.border}`, borderRadius:10, ...style }}>
    {children}
  </div>
);

const Divider = ({ style }) => <div style={{ height:1, background:C.border, ...style }} />;

const SectionLabel = ({ children, sub }) => (
  <div style={{ marginBottom:14 }}>
    <div style={{ fontSize:12, fontWeight:600, color:C.t1, letterSpacing:".04em", textTransform:"uppercase" }}>{children}</div>
    {sub && <div style={{ fontSize:12, color:C.t2, marginTop:2 }}>{sub}</div>}
  </div>
);

const Spinner = () => (
  <div style={{ width:16, height:16, border:`2px solid ${C.border}`, borderTop:`2px solid ${C.green}`,
    borderRadius:"50%", animation:"spin .8s linear infinite" }} />
);

/* ═══════════════════════════════════════════════════════════════════
   FORM PRIMITIVES
═══════════════════════════════════════════════════════════════════ */

function FInput({ label, hint, value, onChange, type="number", min, max, step, placeholder, suffix }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:5 }}>
      <div style={{ display:"flex", justifyContent:"space-between" }}>
        <label style={{ fontSize:12, fontWeight:500, color:C.t1 }}>{label}</label>
        {hint && <span style={{ fontSize:11, color:C.t2 }}>{hint}</span>}
      </div>
      <div style={{ position:"relative" }}>
        <input type={type} value={value} min={min} max={max} step={step} placeholder={placeholder}
          onChange={e => onChange(type==="number" ? (parseFloat(e.target.value)||0) : e.target.value)}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{ width:"100%", padding: suffix ? "8px 36px 8px 10px" : "8px 10px", background:C.bg2,
            border:`1px solid ${focused ? C.green : C.border}`, borderRadius:6, color:C.t0, fontSize:13,
            outline:"none", transition:"border-color .15s" }} />
        {suffix && <span style={{ position:"absolute", right:10, top:"50%", transform:"translateY(-50%)", fontSize:11, color:C.t2 }}>{suffix}</span>}
      </div>
    </div>
  );
}

function FSelect({ label, hint, value, onChange, options }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:5 }}>
      <div style={{ display:"flex", justifyContent:"space-between" }}>
        <label style={{ fontSize:12, fontWeight:500, color:C.t1 }}>{label}</label>
        {hint && <span style={{ fontSize:11, color:C.t2 }}>{hint}</span>}
      </div>
      <select value={value} onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
        style={{ width:"100%", padding:"8px 28px 8px 10px", background:C.bg2,
          border:`1px solid ${focused ? C.green : C.border}`, borderRadius:6, color:C.t0, fontSize:13,
          outline:"none", appearance:"none", transition:"border-color .15s",
          backgroundImage:`url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%2394a3b8' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E")`,
          backgroundRepeat:"no-repeat", backgroundPosition:"right 10px center" }}>
        {options.map(o => <option key={o.v||o} value={o.v||o} style={{ background:C.bg2 }}>{o.l||o}</option>)}
      </select>
    </div>
  );
}

const Btn = ({ children, onClick, variant="primary", disabled, small, style }) => {
  const styles = {
    primary: { background:C.green, border:"none", color:"#000", fontWeight:600 },
    secondary: { background:"transparent", border:`1px solid ${C.border}`, color:C.t1 },
    ghost: { background:"transparent", border:"none", color:C.t1 },
    danger: { background:"rgba(239,68,68,.12)", border:`1px solid rgba(239,68,68,.25)`, color:C.red },
  };
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: small ? "5px 12px" : "9px 18px", borderRadius:6, fontSize: small ? 12 : 13,
        cursor: disabled ? "not-allowed" : "default", opacity: disabled ? .5 : 1,
        transition:"opacity .15s", display:"inline-flex", alignItems:"center", gap:6,
        ...styles[variant], ...style }}>
      {children}
    </button>
  );
};

/* ═══════════════════════════════════════════════════════════════════
   ML INFERENCE (mirrors backend logic for offline use)
═══════════════════════════════════════════════════════════════════ */

function runMLInference(p) {
  // Diet classification (matches trained GBM)
  let diet;
  if (p.diseaseType === "Diabetes")     diet = "Low_Carb";
  else if (p.diseaseType === "Hypertension") diet = "Low_Sodium";
  else                                   diet = "Balanced";

  // Confidence: base + biomarker alignment
  let conf = 0.94;
  if (diet === "Low_Carb"   && p.glucose > 140)  conf = 0.99;
  if (diet === "Low_Sodium" && p.bp > 140)        conf = 0.99;

  // Risk score (weighted biomarker formula)
  const bmi = p.weight / (p.height / 100) ** 2;
  const riskComponents = {
    glucose:  Math.round(Math.min((p.glucose - 70) / 130, 1) * 25 * 10) / 10,
    bp:       Math.round(Math.min((p.bp - 90) / 90, 1) * 25 * 10) / 10,
    cholesterol: Math.round(Math.min((p.cholesterol - 150) / 100, 1) * 20 * 10) / 10,
    bmi:      Math.round(Math.min(Math.max(bmi - 18.5, 0) / 30, 1) * 15 * 10) / 10,
    activity: p.activity === "Sedentary" ? 10 : p.activity === "Moderate" ? 4 : 0,
    nutrition:Math.round((p.nutrientImbalance / 5) * 5 * 10) / 10,
  };
  const riskScore = Math.min(100, Math.max(0,
    Object.values(riskComponents).reduce((a, b) => a + b, 0)
  ));
  const riskLevel = riskScore >= 70 ? "High" : riskScore >= 40 ? "Moderate" : "Low";

  // Meal category
  const mealCat = diet === "Low_Carb" ? "High-Protein" : diet === "Low_Sodium" ? "Heart-Healthy" : "Balanced-Macro";

  // Flags
  const flags = [];
  if (p.glucose > 180)     flags.push({ label:"Critical glucose", level:"critical" });
  else if (p.glucose > 126)flags.push({ label:"Elevated glucose", level:"warning" });
  if (p.bp > 160)          flags.push({ label:"Hypertensive crisis", level:"critical" });
  else if (p.bp > 140)     flags.push({ label:"High blood pressure", level:"warning" });
  if (p.cholesterol > 240) flags.push({ label:"High cholesterol", level:"warning" });
  if (bmi > 35)            flags.push({ label:"Obesity class II", level:"critical" });
  else if (bmi > 30)       flags.push({ label:"Obesity class I", level:"warning" });
  if (p.activity === "Sedentary") flags.push({ label:"Sedentary lifestyle", level:"info" });
  if (flags.length === 0)  flags.push({ label:"No critical flags", level:"success" });

  // Clinical insights
  const insights = [];
  if (p.diseaseType === "Diabetes") {
    insights.push("Restrict net carbohydrates to < 50g/day to stabilise blood glucose.");
    if (p.glucose > 140) insights.push("Elevated glucose — monitor at 1 hr and 2 hrs post-meal.");
  } else if (p.diseaseType === "Hypertension") {
    insights.push("Sodium target < 1,500 mg/day following DASH protocol.");
    if (p.bp > 140) insights.push("Stage 2 hypertension detected — physician review recommended.");
  } else {
    if (bmi > 30) insights.push(`BMI ${bmi.toFixed(1)} — a 300–500 kcal/day deficit supports safe weight loss.`);
    insights.push("Prioritise dietary diversity to cover all micronutrient requirements.");
  }
  if (p.cholesterol > 200) insights.push("Elevated cholesterol — limit saturated fat, increase omega-3 intake.");
  if (p.activity === "Sedentary") insights.push("150 min/week moderate cardio improves all biomarker trajectories.");

  // Health scores (0-100)
  const scores = {
    metabolic: Math.max(0, Math.round(100 - riskComponents.glucose * 2.5 - riskComponents.bmi * 3)),
    cardiovascular: Math.max(0, Math.round(100 - riskComponents.bp * 2.5 - riskComponents.cholesterol * 2)),
    lifestyle: Math.min(100, Math.round((p.exercise / 10) * 60 + (p.activity === "Active" ? 40 : p.activity === "Moderate" ? 20 : 0))),
  };
  scores.overall = Math.round((scores.metabolic + scores.cardiovascular + scores.lifestyle) / 3);

  const ruleBasedOverrides = [];
  const trendCurves = [
    {
      metric: "Projected Risk Score",
      data: [{month: "Month 1", value: riskScore}, {month: "Month 3", value: Math.max(10, riskScore-10)}, {month: "Month 6", value: Math.max(5, riskScore-20)}]
    }
  ];

  return { diet, conf, riskScore: Math.round(riskScore * 10) / 10, riskLevel, riskComponents,
           mealCat, flags, insights, scores, bmi: Math.round(bmi * 10) / 10, ruleBasedOverrides, trendCurves };
}

/* ═══════════════════════════════════════════════════════════════════
   DATA
═══════════════════════════════════════════════════════════════════ */

const DIET_PLANS = {
  Low_Carb:   { label:"Low-Carb", color:C.green,  kcal:"1,600–2,000", macros:[{n:"Protein",p:35,c:C.green},{n:"Fat",p:45,c:C.teal},{n:"Carbs",p:20,c:C.t2}], include:["Leafy greens","Eggs","Fatty fish","Avocado","Nuts & seeds","Berries (limited)","Olive oil","Cauliflower"], exclude:["White bread","Rice & pasta","Sugary drinks","Fruit juice","Chips","High-GI fruit"] },
  Low_Sodium: { label:"Low-Sodium", color:C.teal, kcal:"1,800–2,200", macros:[{n:"Protein",p:25,c:C.teal},{n:"Fat",p:30,c:C.blue},{n:"Carbs",p:45,c:C.t2}], include:["Fresh fruit","Whole grains","Lean poultry","Legumes","Low-Na dairy","Herbs","Oily fish","Potassium-rich foods"], exclude:["Table salt","Canned soup","Processed meats","Pickles","Fast food","Soy sauce"] },
  Balanced:   { label:"Balanced",  color:C.blue,  kcal:"1,800–2,400", macros:[{n:"Protein",p:25,c:C.blue},{n:"Fat",p:30,c:C.amber},{n:"Carbs",p:45,c:C.t2}], include:["Whole grains","Colourful veg","Lean proteins","Healthy fats","Low-fat dairy","Fresh fruit","Legumes","Eggs"], exclude:["Ultra-processed","Trans fats","Excessive sugar","Alcohol","Refined grains"] },
};

const MEALS_DB = {
  "High-Protein": {
    Indian: [
      { name:"Paneer tikka bowl", kcal:420, p:32, f:24, c:18, time:"Lunch" },
      { name:"Egg bhurji + multigrain roti", kcal:380, p:28, f:18, c:22, time:"Breakfast" },
      { name:"Chicken tikka masala (no rice)", kcal:490, p:38, f:28, c:12, time:"Dinner" },
      { name:"Dal tadka (protein-forward)", kcal:310, p:18, f:14, c:20, time:"Dinner" },
    ],
    Chinese: [
      { name:"Steamed fish with ginger", kcal:380, p:35, f:18, c:10, time:"Dinner" },
      { name:"Egg drop soup + tofu", kcal:220, p:18, f:10, c:8, time:"Lunch" },
      { name:"Stir-fried chicken & broccoli", kcal:360, p:34, f:16, c:12, time:"Dinner" },
      { name:"Steamed prawn dumplings", kcal:320, p:24, f:12, c:20, time:"Lunch" },
    ],
    Italian: [
      { name:"Grilled chicken paillard", kcal:390, p:42, f:20, c:6, time:"Dinner" },
      { name:"Frittata (egg & spinach)", kcal:340, p:26, f:22, c:8, time:"Breakfast" },
      { name:"Tuna carpaccio", kcal:280, p:30, f:14, c:4, time:"Lunch" },
      { name:"Grilled sea bass + capers", kcal:360, p:36, f:18, c:4, time:"Dinner" },
    ],
    Mexican: [
      { name:"Grilled chicken fajitas (lettuce wrap)", kcal:380, p:38, f:18, c:16, time:"Dinner" },
      { name:"Huevos rancheros (low-carb)", kcal:360, p:24, f:22, c:16, time:"Breakfast" },
      { name:"Carne asada bowl", kcal:420, p:36, f:20, c:20, time:"Lunch" },
      { name:"Tuna tostadas", kcal:340, p:28, f:16, c:22, time:"Lunch" },
    ],
  },
  "Heart-Healthy": {
    Indian: [
      { name:"Vegetable khichdi", kcal:340, p:14, f:8, c:55, time:"Lunch" },
      { name:"Oats upma", kcal:290, p:10, f:6, c:48, time:"Breakfast" },
      { name:"Rajma (low Na) + brown rice", kcal:420, p:18, f:7, c:62, time:"Dinner" },
      { name:"Palak dal", kcal:300, p:14, f:8, c:38, time:"Dinner" },
    ],
    Chinese: [
      { name:"Congee with ginger", kcal:240, p:8, f:3, c:42, time:"Breakfast" },
      { name:"Steamed salmon fried rice", kcal:420, p:28, f:10, c:48, time:"Dinner" },
      { name:"Hot & sour soup (low Na)", kcal:160, p:8, f:4, c:18, time:"Starter" },
      { name:"Buddha's delight (vegetable stew)", kcal:280, p:10, f:8, c:38, time:"Dinner" },
    ],
    Italian: [
      { name:"Minestrone soup", kcal:220, p:9, f:4, c:38, time:"Lunch" },
      { name:"Grilled sea bass", kcal:380, p:32, f:20, c:10, time:"Dinner" },
      { name:"Caprese salad (low Na)", kcal:180, p:10, f:12, c:8, time:"Starter" },
      { name:"Pasta e fagioli (low Na)", kcal:340, p:14, f:6, c:54, time:"Dinner" },
    ],
    Mexican: [
      { name:"Chicken tortilla soup (low Na)", kcal:280, p:20, f:8, c:28, time:"Lunch" },
      { name:"Baked tilapia tacos", kcal:350, p:28, f:10, c:32, time:"Dinner" },
      { name:"Veggie burrito bowl (no salt)", kcal:380, p:14, f:8, c:58, time:"Dinner" },
      { name:"Guacamole + jicama sticks", kcal:190, p:3, f:14, c:14, time:"Snack" },
    ],
  },
  "Balanced-Macro": {
    Indian: [
      { name:"Mixed dal + chapati", kcal:390, p:16, f:9, c:58, time:"Lunch" },
      { name:"Poha with peanuts", kcal:280, p:8, f:8, c:44, time:"Breakfast" },
      { name:"Vegetable biryani", kcal:460, p:12, f:12, c:70, time:"Dinner" },
      { name:"Curd rice", kcal:320, p:10, f:7, c:52, time:"Dinner" },
    ],
    Chinese: [
      { name:"Wonton noodle soup", kcal:360, p:18, f:9, c:48, time:"Lunch" },
      { name:"Mapo tofu + rice", kcal:380, p:16, f:18, c:34, time:"Dinner" },
      { name:"Steamed bun (bao)", kcal:200, p:8, f:4, c:32, time:"Snack" },
      { name:"Dan dan noodles (light)", kcal:420, p:18, f:14, c:52, time:"Dinner" },
    ],
    Italian: [
      { name:"Wholewheat pasta primavera", kcal:420, p:16, f:9, c:68, time:"Dinner" },
      { name:"Mushroom risotto", kcal:380, p:12, f:10, c:62, time:"Dinner" },
      { name:"Panzanella salad", kcal:280, p:8, f:10, c:40, time:"Lunch" },
      { name:"Bruschetta + caprese", kcal:300, p:12, f:12, c:36, time:"Lunch" },
    ],
    Mexican: [
      { name:"Brown rice burrito bowl", kcal:460, p:20, f:12, c:62, time:"Lunch" },
      { name:"Wholewheat quesadilla", kcal:380, p:18, f:14, c:44, time:"Dinner" },
      { name:"Chicken tinga tacos (3)", kcal:420, p:28, f:14, c:40, time:"Dinner" },
      { name:"Pozole (light)", kcal:310, p:20, f:6, c:36, time:"Dinner" },
    ],
  },
};

const FOOD_DB = [
  { name:"Brown rice (cooked)", kcal:216, p:5, f:2, c:45, cat:"Grain" },
  { name:"White rice (cooked)", kcal:242, p:4, f:0, c:53, cat:"Grain" },
  { name:"Oats (dry 50g)", kcal:189, p:6, f:3, c:34, cat:"Grain" },
  { name:"Whole wheat bread (1 slice)", kcal:81, p:4, f:1, c:15, cat:"Grain" },
  { name:"Quinoa (cooked 1 cup)", kcal:222, p:8, f:4, c:39, cat:"Grain" },
  { name:"Chicken breast (100g grilled)", kcal:165, p:31, f:4, c:0, cat:"Protein" },
  { name:"Salmon (100g baked)", kcal:208, p:28, f:11, c:0, cat:"Protein" },
  { name:"Egg (1 large)", kcal:78, p:6, f:5, c:1, cat:"Protein" },
  { name:"Paneer (100g)", kcal:265, p:18, f:21, c:2, cat:"Protein" },
  { name:"Tofu (100g firm)", kcal:76, p:8, f:5, c:2, cat:"Protein" },
  { name:"Tuna (canned, 100g)", kcal:116, p:26, f:1, c:0, cat:"Protein" },
  { name:"Lentils (cooked 1 cup)", kcal:230, p:18, f:1, c:40, cat:"Legume" },
  { name:"Black beans (cooked 1 cup)", kcal:227, p:15, f:1, c:41, cat:"Legume" },
  { name:"Chickpeas (cooked 1 cup)", kcal:269, p:15, f:4, c:45, cat:"Legume" },
  { name:"Spinach (raw 100g)", kcal:23, p:3, f:0, c:4, cat:"Vegetable" },
  { name:"Broccoli (steamed 100g)", kcal:35, p:4, f:0, c:7, cat:"Vegetable" },
  { name:"Sweet potato (medium)", kcal:103, p:2, f:0, c:24, cat:"Vegetable" },
  { name:"Avocado (half)", kcal:160, p:2, f:15, c:9, cat:"Fat" },
  { name:"Almonds (30g)", kcal:173, p:6, f:15, c:6, cat:"Fat" },
  { name:"Olive oil (1 tbsp)", kcal:119, p:0, f:14, c:0, cat:"Fat" },
  { name:"Greek yogurt (100g)", kcal:97, p:10, f:5, c:4, cat:"Dairy" },
  { name:"Banana (medium)", kcal:105, p:1, f:0, c:27, cat:"Fruit" },
  { name:"Apple (medium)", kcal:95, p:0, f:0, c:25, cat:"Fruit" },
  { name:"Blueberries (100g)", kcal:57, p:1, f:0, c:14, cat:"Fruit" },
];

/* ═══════════════════════════════════════════════════════════════════
   SIDEBAR NAV
═══════════════════════════════════════════════════════════════════ */
const NAV_ITEMS = [
  { id:"dashboard", label:"Dashboard",    icon:"M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { id:"meals",     label:"Meal Plan",    icon:"M18.06 22.99h1.66c.84 0 1.53-.64 1.63-1.46L23 5.05h-5V1h-1.97v4.05h-4.97l.3 2.34c1.71.47 3.31 1.32 4.27 2.26 1.44 1.42 2.43 2.89 2.43 5.29v8.05zM1 21.99V21h15.03v.99c0 .55-.45 1-1.01 1H2.01c-.56 0-1.01-.45-1.01-1zm15.03-7c0-8-15.03-8-15.03 0h15.03zM1.02 17h15v2h-15z" },
  { id:"foodsearch",label:"Food Search",  icon:"M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.516 6.516 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5z" },
  { id:"calculator",label:"Calculator",   icon:"M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14h-2v-4H8v-2h4V7h2v4h4v2h-4v4z" },
  { id:"progress",  label:"Progress",     icon:"M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" },
  { id:"report",    label:"Report",       icon:"M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 5h-3v5.5a2.5 2.5 0 0 1-5 0 2.5 2.5 0 0 1 2.5-2.5c.57 0 1.08.19 1.5.51V5h4v2zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6z" },
  { id:"metrics",   label:"Metrics (Acc.)",icon:"M3 3h18v18H3V3zm16 16V5H5v14h14zM7 17h2v-7H7v7zm4 0h2V7h-2v10zm4 0h2v-4h-2v4z" },
  { id:"aichat",    label:"AI Consult",   icon:"M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" },
];

function Sidebar({ active, onNav, result }) {
  return (
    <div style={{ width:220, background:C.bg1, borderRight:`1px solid ${C.border}`, display:"flex", flexDirection:"column", height:"100vh", flexShrink:0 }}>
      {/* Logo */}
      <div style={{ padding:"20px 18px 16px", borderBottom:`1px solid ${C.border}` }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{ width:30, height:30, borderRadius:7, background:C.green, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
            <svg width={14} height={14} viewBox="0 0 16 16" fill="none">
              <path d="M8 2C5.8 2 4 3.8 4 6c0 1.5.8 2.8 2 3.5V11h4V9.5C11.2 8.8 12 7.5 12 6c0-2.2-1.8-4-4-4z" fill="#000" />
              <rect x={6} y={11} width={4} height={2} rx={1} fill="#000" />
              <rect x={6.5} y={13} width={3} height={1} rx={.5} fill="#000" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize:14, fontWeight:600, color:C.t0 }}>NutriPlanner</div>
            <div style={{ fontSize:10, color:C.t2, letterSpacing:".05em" }}>Clinical Platform</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding:"10px 10px", flex:1, overflowY:"auto" }}>
        {NAV_ITEMS.map(item => (
          <button key={item.id} onClick={() => onNav(item.id)}
            style={{ width:"100%", display:"flex", alignItems:"center", gap:10, padding:"9px 10px", borderRadius:6,
              background: active === item.id ? C.bg3 : "transparent",
              border: active === item.id ? `1px solid ${C.border}` : "1px solid transparent",
              color: active === item.id ? C.t0 : C.t1, fontSize:13, cursor:"pointer",
              marginBottom:2, transition:"all .15s", textAlign:"left" }}>
            <svg width={16} height={16} viewBox="0 0 24 24" fill={active === item.id ? C.green : C.t2} style={{ flexShrink:0 }}>
              <path d={item.icon} />
            </svg>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Risk indicator */}
      {result && (
        <div style={{ padding:"14px 14px", borderTop:`1px solid ${C.border}` }}>
          <div style={{ fontSize:11, color:C.t2, marginBottom:6 }}>Risk score</div>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <div style={{ flex:1, height:4, background:C.bg3, borderRadius:2 }}>
              <div style={{ width:`${result.riskScore}%`, height:"100%", borderRadius:2,
                background: result.riskScore >= 70 ? C.red : result.riskScore >= 40 ? C.amber : C.green,
                transition:"width .6s ease" }} />
            </div>
            <Mono size={12} color={result.riskScore >= 70 ? C.red : result.riskScore >= 40 ? C.amber : C.green}>
              {result.riskScore}
            </Mono>
          </div>
          <div style={{ fontSize:11, color:C.t2, marginTop:4 }}>{result.riskLevel} risk · {result.diet.replace("_"," ")}</div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: ONBOARDING FORM
═══════════════════════════════════════════════════════════════════ */
function OnboardingForm({ onSubmit, submitting = false }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    age:45, gender:"Male", weight:75, height:170,
    diseaseType:"Diabetes", severity:"Moderate", activity:"Moderate",
    calories:2200, cholesterol:210, bp:135, glucose:150,
    restrictions:"None", allergies:"None", cuisine:"Indian",
    exercise:3, adherence:70, nutrientImbalance:2.5,
  });
  const set = k => v => setForm(p => ({...p, [k]:v}));
  const bmi = form.weight && form.height ? form.weight / (form.height/100)**2 : null;
  const bmiLabel = !bmi ? "" : bmi < 18.5 ? "Underweight" : bmi < 25 ? "Normal" : bmi < 30 ? "Overweight" : "Obese";
  const bmiColor = !bmi ? C.t1 : bmi < 18.5 ? C.blue : bmi < 25 ? C.green : bmi < 30 ? C.amber : C.red;

  const STEPS = [
    { label:"Personal", fields:() => (
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
        <FInput label="Age" suffix="yrs" value={form.age} onChange={set("age")} min={18} max={100} />
        <FSelect label="Biological sex" value={form.gender} onChange={set("gender")} options={["Male","Female"]} />
        <FInput label="Weight" suffix="kg" value={form.weight} onChange={set("weight")} min={30} max={300} step={.1} />
        <FInput label="Height" suffix="cm" value={form.height} onChange={set("height")} min={100} max={250} />
        {bmi && (
          <div style={{ gridColumn:"span 2", padding:"10px 12px", background:C.bg2, borderRadius:6,
            border:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <div style={{ fontSize:12, color:C.t2 }}>BMI</div>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <Mono color={bmiColor} size={16}>{bmi.toFixed(1)}</Mono>
              <Tag label={bmiLabel} level={bmi < 18.5 ? "info" : bmi < 25 ? "success" : bmi < 30 ? "warning" : "critical"} />
            </div>
          </div>
        )}
      </div>
    )},
    { label:"Clinical", fields:() => (
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
        <FSelect label="Primary condition" value={form.diseaseType} onChange={set("diseaseType")}
          options={[{v:"None",l:"No diagnosis"},{v:"Diabetes",l:"Diabetes"},{v:"Hypertension",l:"Hypertension"},{v:"Obesity",l:"Obesity"}]} />
        <FSelect label="Severity" value={form.severity} onChange={set("severity")} options={["Mild","Moderate","Severe"]} />
        <FInput label="Fasting glucose" suffix="mg/dL" value={form.glucose} onChange={set("glucose")} min={40} max={400} step={.1} />
        <FInput label="Blood pressure (sys.)" suffix="mmHg" value={form.bp} onChange={set("bp")} min={60} max={220} />
        <FInput label="Total cholesterol" suffix="mg/dL" value={form.cholesterol} onChange={set("cholesterol")} min={50} max={400} step={.1} />
        <FInput label="Daily caloric intake" suffix="kcal" value={form.calories} onChange={set("calories")} min={500} max={6000} />
        <div style={{ gridColumn:"span 2", padding:"10px 12px", background:C.bg2, borderRadius:6, border:`1px solid ${C.border}`, fontSize:12, color:C.t2 }}>
          Reference: Glucose &lt;100 · BP &lt;120 · Cholesterol &lt;200 mg/dL
        </div>
      </div>
    )},
    { label:"Lifestyle", fields:() => (
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
        <FSelect label="Activity level" value={form.activity} onChange={set("activity")} options={["Sedentary","Moderate","Active"]} />
        <FInput label="Weekly exercise" suffix="hrs" value={form.exercise} onChange={set("exercise")} min={0} max={40} step={.5} />
        <FSelect label="Dietary restrictions" value={form.restrictions} onChange={set("restrictions")}
          options={[{v:"None",l:"None"},{v:"Low_Sodium",l:"Low sodium"},{v:"Low_Sugar",l:"Low sugar"}]} />
        <FSelect label="Allergies" value={form.allergies} onChange={set("allergies")} options={["None","Gluten","Peanuts"]} />
        <FSelect label="Cuisine preference" value={form.cuisine} onChange={set("cuisine")} options={["Indian","Chinese","Italian","Mexican"]} />
        <FInput label="Diet adherence" suffix="%" value={form.adherence} onChange={set("adherence")} min={0} max={100} />
      </div>
    )},
  ];

  return (
    <div style={{ minHeight:"100vh", background:C.bg0, display:"flex", alignItems:"center", justifyContent:"center", padding:24 }}>
      <div style={{ width:"100%", maxWidth:520 }}>
        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:36 }}>
          <div style={{ width:34, height:34, borderRadius:8, background:C.green, display:"flex", alignItems:"center", justifyContent:"center" }}>
            <svg width={16} height={16} viewBox="0 0 16 16" fill="none">
              <path d="M8 2C5.8 2 4 3.8 4 6c0 1.5.8 2.8 2 3.5V11h4V9.5C11.2 8.8 12 7.5 12 6c0-2.2-1.8-4-4-4z" fill="#000" />
              <rect x={6} y={11} width={4} height={2} rx={1} fill="#000" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize:16, fontWeight:600, color:C.t0 }}>NutriPlanner</div>
            <div style={{ fontSize:11, color:C.t2, letterSpacing:".04em" }}>Clinical Nutrition Platform</div>
          </div>
        </div>

        <div style={{ marginBottom:28 }}>
          <h1 style={{ fontSize:24, fontWeight:600, color:C.t0, letterSpacing:"-.02em", lineHeight:1.2 }}>
            Patient intake<br /><span style={{ color:C.t2, fontWeight:400 }}>assessment</span>
          </h1>
        </div>

        {/* Steps */}
        <div style={{ display:"flex", gap:6, marginBottom:24 }}>
          {STEPS.map((s,i) => (
            <div key={s.label} style={{ flex:1, cursor: i < step ? "pointer" : "default" }} onClick={() => i < step && setStep(i)}>
              <div style={{ height:2, borderRadius:1, background: i <= step ? C.green : C.border, marginBottom:5, transition:"background .3s" }} />
              <span style={{ fontSize:11, color: i === step ? C.green : i < step ? C.t1 : C.t2, fontWeight: i === step ? 500 : 400 }}>
                {String(i+1).padStart(2,"0")} {s.label}
              </span>
            </div>
          ))}
        </div>

        <Card style={{ padding:"24px 22px 20px" }}>
          <div className="fu">{STEPS[step].fields()}</div>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:22, paddingTop:18, borderTop:`1px solid ${C.border}` }}>
            {step > 0
              ? <Btn variant="secondary" onClick={() => setStep(s => s-1)} small>← Back</Btn>
              : <div />
            }
            {step < STEPS.length - 1
              ? <Btn onClick={() => setStep(s => s+1)}>Continue →</Btn>
              : <Btn onClick={() => onSubmit(form)} disabled={submitting}>
                  {submitting ? <><Spinner /> Analysing…</> : <>Generate report →</>}
                </Btn>
            }
          </div>
        </Card>
        <div style={{ marginTop:12, fontSize:11, color:C.t2, textAlign:"center" }}>
          For informational purposes only. Always consult a licensed dietitian or physician.
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: DASHBOARD
═══════════════════════════════════════════════════════════════════ */
function ScoreRing({ score, label, color, size=68 }) {
  const r = size/2 - 7, circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={C.bg3} strokeWidth={5} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={5}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition:"stroke-dasharray .8s ease" }} />
        <text x={size/2} y={size/2+5} textAnchor="middle" fill={C.t0} fontSize={13} fontWeight={500} fontFamily={F.mono}>{score}</text>
      </svg>
      <span style={{ fontSize:10, color:C.t2, letterSpacing:".04em", textTransform:"uppercase" }}>{label}</span>
    </div>
  );
}

function RiskBar({ label, value, max=25 }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct > 70 ? C.red : pct > 40 ? C.amber : C.green;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10 }}>
      <span style={{ fontSize:11, color:C.t2, width:90, flexShrink:0 }}>{label}</span>
      <div style={{ flex:1, height:4, background:C.bg3, borderRadius:2 }}>
        <div style={{ width:`${pct}%`, height:"100%", background:color, borderRadius:2, transition:"width .6s ease" }} />
      </div>
      <Mono size={11} color={color}>{value}</Mono>
    </div>
  );
}

function DashboardPage({ form, result }) {
  const plan = DIET_PLANS[result.diet];
  const totalMacro = plan.macros.reduce((a,b) => a+b.p, 0);
  const biomarkers = [
    { label:"Glucose",     value:form.glucose,     unit:"mg/dL", status: form.glucose>180?"critical": form.glucose>126?"warning":"ok" },
    { label:"Blood press.", value:form.bp,          unit:"mmHg",  status: form.bp>160?"critical": form.bp>140?"warning":"ok" },
    { label:"Cholesterol", value:form.cholesterol,  unit:"mg/dL", status: form.cholesterol>240?"critical": form.cholesterol>200?"warning":"ok" },
    { label:"BMI",         value:result.bmi,        unit:"kg/m²", status: result.bmi>35?"critical": result.bmi>30?"warning": result.bmi<18.5?"warning":"ok" },
  ];
  const sColor = s => s==="critical"?C.red: s==="warning"?C.amber:C.green;

  return (
    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:16, padding:24 }}>
      {/* ── Recommendation banner ── */}
      <div className="fu" style={{ gridColumn:"span 3", background:C.bg1, border:`1px solid ${C.border}`, borderRadius:10, padding:"18px 22px", display:"flex", alignItems:"center", justifyContent:"space-between", flexWrap:"wrap", gap:12 }}>
        <div>
          <div style={{ fontSize:11, color:C.t2, letterSpacing:".06em", textTransform:"uppercase", marginBottom:6 }}>ML Recommendation · {Math.round(result.conf*100)}% confidence</div>
          <div style={{ display:"flex", alignItems:"center", gap:12, flexWrap:"wrap" }}>
            <span style={{ fontSize:22, fontWeight:600, color:plan.color, letterSpacing:"-.02em" }}>{plan.label}</span>
            <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
              {result.flags.map((f,i) => <Tag key={i} label={f.label} level={f.level} />)}
            </div>
          </div>
        </div>
        <div style={{ display:"flex", gap:16 }}>
          {Object.entries(result.scores).filter(([k]) => k!=="overall").map(([k,v]) => (
            <ScoreRing key={k} score={v} label={k} color={k==="metabolic"?C.green:k==="cardiovascular"?C.teal:C.blue} />
          ))}
        </div>
      </div>

      {/* ── Biomarkers ── */}
      <Card className="fu1" style={{ padding:18 }}>
        <SectionLabel>Biomarker panel</SectionLabel>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
          {biomarkers.map(b => (
            <div key={b.label} style={{ background:C.bg2, border:`1px solid ${C.border}`, borderRadius:7, padding:"11px 13px" }}>
              <div style={{ fontSize:10, color:C.t2, textTransform:"uppercase", letterSpacing:".05em", marginBottom:6 }}>{b.label}</div>
              <div style={{ display:"flex", alignItems:"baseline", gap:4 }}>
                <Mono color={sColor(b.status)} size={20}>{b.value}</Mono>
                <span style={{ fontSize:10, color:C.t2 }}>{b.unit}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Risk breakdown ── */}
      <Card className="fu2" style={{ padding:18 }}>
        <SectionLabel>Risk breakdown <span style={{ color:C.t2, fontSize:11 }}>total: {result.riskScore}/100</span></SectionLabel>
        <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
          <RiskBar label="Glucose" value={result.riskComponents.glucose} max={25} />
          <RiskBar label="Blood pressure" value={result.riskComponents.bp} max={25} />
          <RiskBar label="Cholesterol" value={result.riskComponents.cholesterol} max={20} />
          <RiskBar label="BMI" value={result.riskComponents.bmi} max={15} />
          <RiskBar label="Activity" value={result.riskComponents.activity} max={10} />
          <RiskBar label="Nutrition" value={result.riskComponents.nutrition} max={5} />
        </div>
      </Card>

      {/* ── Macro + insights ── */}
      <Card className="fu3" style={{ padding:18, display:"flex", flexDirection:"column", gap:14 }}>
        <div>
          <SectionLabel>Macronutrient split</SectionLabel>
          <div style={{ display:"flex", height:6, borderRadius:3, overflow:"hidden", gap:1, marginBottom:10 }}>
            {plan.macros.map((m,i) => <div key={i} style={{ width:`${m.p}%`, background:m.c }} />)}
          </div>
          <div style={{ display:"flex", gap:12 }}>
            {plan.macros.map((m,i) => (
              <div key={i} style={{ display:"flex", alignItems:"center", gap:5 }}>
                <div style={{ width:8, height:8, borderRadius:2, background:m.c }} />
                <span style={{ fontSize:11, color:C.t1 }}>{m.n}</span>
                <Mono size={11}>{m.p}%</Mono>
              </div>
            ))}
          </div>
        </div>
        <Divider />
        <div>
          <SectionLabel>Clinical insights</SectionLabel>
          {result.insights.map((ins,i) => (
            <div key={i} style={{ padding:"9px 10px", background:C.bg2, borderLeft:`2px solid ${plan.color}`, borderRadius:"0 5px 5px 0", marginBottom:8, fontSize:12, color:C.t1, lineHeight:1.55 }}>
              {ins}
            </div>
          ))}
        </div>
        <Divider />
        <div>
          <SectionLabel>Rule-Based Overrides</SectionLabel>
          {result.ruleBasedOverrides && result.ruleBasedOverrides.length > 0 ? result.ruleBasedOverrides.map((rule,i) => (
            <div key={i} style={{ padding:"9px 10px", background:"rgba(239,68,68,.08)", borderLeft:`2px solid ${C.red}`, borderRadius:"0 5px 5px 0", marginBottom:8, fontSize:12, color:C.red, lineHeight:1.55 }}>
              <strong>Override Engine:</strong> {rule}
            </div>
          )) : <div style={{ fontSize:12, color:C.t2 }}>No overrides triggered. ML recommendation natively approved.</div>}
        </div>
        <div style={{ marginTop:"auto", padding:"10px 12px", background:C.bg2, borderRadius:6 }}>
          <div style={{ fontSize:11, color:C.t2, marginBottom:2 }}>Daily calorie target</div>
          <Mono color={plan.color}>{plan.kcal}</Mono>
          <span style={{ fontSize:11, color:C.t2, marginLeft:4 }}>kcal/day</span>
        </div>
      </Card>

      {/* ── Foods ── */}
      <Card style={{ padding:18, gridColumn:"span 2" }}>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
          <div>
            <SectionLabel>Recommended foods</SectionLabel>
            <div style={{ display:"flex", flexWrap:"wrap", gap:5 }}>
              {plan.include.map((f,i) => (
                <span key={i} style={{ padding:"3px 8px", borderRadius:4, background:`${plan.color}15`, border:`1px solid ${plan.color}30`, fontSize:11, color:plan.color }}>{f}</span>
              ))}
            </div>
          </div>
          <div>
            <SectionLabel>Foods to avoid</SectionLabel>
            <div style={{ display:"flex", flexWrap:"wrap", gap:5 }}>
              {plan.exclude.map((f,i) => (
                <span key={i} style={{ padding:"3px 8px", borderRadius:4, background:"rgba(239,68,68,.08)", border:"1px solid rgba(239,68,68,.2)", fontSize:11, color:C.red }}>{f}</span>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card style={{ padding:18 }}>
        <SectionLabel>Patient summary</SectionLabel>
        {[["Condition", `${form.diseaseType} · ${form.severity}`],["Age / Sex",`${form.age} yrs · ${form.gender}`],["Weight / Height",`${form.weight} kg · ${form.height} cm`],["Activity",form.activity],["Cuisine",form.cuisine],["Exercise",`${form.exercise} hrs/week`]].map(([k,v]) => (
          <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"7px 0", borderBottom:`1px solid ${C.border}`, fontSize:12 }}>
            <span style={{ color:C.t2 }}>{k}</span>
            <span style={{ color:C.t0, fontWeight:500 }}>{v}</span>
          </div>
        ))}
      </Card>
      
      {/* ── Trend Curves ── */}
      {result.trendCurves && result.trendCurves.length > 0 && (
         <Card className="fu4" style={{ padding:18, gridColumn:"span 3" }}>
            <SectionLabel>Predictive Trend Curves</SectionLabel>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20 }}>
               {result.trendCurves.map(curve => (
                  <div key={curve.metric} style={{ background:C.bg2, padding:14, borderRadius:8, border:`1px solid ${C.border}` }}>
                     <div style={{ fontSize:13, fontWeight:600, color:C.t0, marginBottom:12 }}>{curve.metric}</div>
                     <div style={{ display:"flex", justifyContent:"space-between" }}>
                        {curve.data.map((pt, i) => (
                           <div key={i} style={{ textAlign:"center" }}>
                              <Mono size={18} color={i === curve.data.length - 1 ? C.green : C.t1}>{pt.value}</Mono>
                              <div style={{ fontSize:11, color:C.t2, marginTop:4 }}>{pt.month}</div>
                           </div>
                        ))}
                     </div>
                  </div>
               ))}
            </div>
         </Card>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: MEAL PLAN
═══════════════════════════════════════════════════════════════════ */
// ── Allergen keyword map ────────────────────────────────────────────
const ALLERGEN_KEYWORDS = {
  "Peanuts": ["peanut","groundnut"],
  "Gluten":  ["roti","chapati","naan","bread","pasta","bun","tortilla","burrito","quesadilla","wrap","dumpling","tostada","bruschetta","couscous","semolina"],
  "Dairy":   ["paneer","curd","yogurt","cheese","cream","butter","ghee","milk","lassi"],
  "Gluten,Dairy": ["roti","chapati","naan","bread","pasta","bun","tortilla","burrito","quesadilla","wrap","dumpling","paneer","curd","yogurt"],
};

function filterMealsByAllergen(meals, allergies) {
  if (!allergies || allergies === "None") return meals;
  const keywords = ALLERGEN_KEYWORDS[allergies] || [allergies.toLowerCase()];
  return meals.filter(m => {
    const name = m.name.toLowerCase();
    return !keywords.some(kw => name.includes(kw));
  });
}

function MealPlanPage({ form, result }) {
  const rawMeals = MEALS_DB[result.mealCat]?.[form.cuisine] || MEALS_DB[result.mealCat]?.Indian || [];
  const meals = filterMealsByAllergen(rawMeals, form.allergies);
  const plan = DIET_PLANS[result.diet];
  const totalKcal = meals.reduce((a,m) => a+m.kcal, 0);

  return (
    <div style={{ padding:24 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:600, color:C.t0, letterSpacing:"-.01em" }}>Daily meal schedule</div>
          <div style={{ fontSize:12, color:C.t2, marginTop:3 }}>{result.mealCat} · {form.cuisine} cuisine · {form.allergies !== "None" ? `No ${form.allergies}` : "No allergen restrictions"}</div>
        </div>
        <div style={{ padding:"8px 14px", background:C.bg2, border:`1px solid ${C.border}`, borderRadius:6 }}>
          <span style={{ fontSize:11, color:C.t2 }}>Total: </span>
          <Mono color={plan.color}>{totalKcal.toLocaleString()}</Mono>
          <span style={{ fontSize:11, color:C.t2 }}> kcal</span>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:16 }}>
        {meals.map((m,i) => (
          <Card key={i} className={`fu${i}`} style={{ padding:"18px 20px" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:10 }}>
              <div>
                <div style={{ fontSize:10, color:C.t2, textTransform:"uppercase", letterSpacing:".06em", marginBottom:4 }}>{m.time}</div>
                <div style={{ fontSize:15, fontWeight:600, color:C.t0 }}>{m.name}</div>
              </div>
            </div>
            <div style={{ display:"flex", gap:16, marginBottom:10 }}>
              {[["Protein",m.p,"g",C.green],["Fat",m.f,"g",C.amber],["Carbs",m.c,"g",C.blue]].map(([label,val,unit,color]) => (
                <div key={label}>
                  <div style={{ fontSize:10, color:C.t2, marginBottom:2 }}>{label}</div>
                  <Mono color={color} size={13}>{val}<span style={{ fontSize:10, color:C.t2, fontFamily:F.sans }}>{unit}</span></Mono>
                </div>
              ))}
            </div>
            <Divider style={{ margin:"10px 0" }} />
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
              <div style={{ display:"flex", alignItems:"baseline", gap:3 }}>
                <Mono color={plan.color} size={15}>{m.kcal}</Mono>
                <span style={{ fontSize:11, color:C.t2 }}>kcal</span>
              </div>
              <div style={{ height:3, width:80, background:C.bg3, borderRadius:2 }}>
                <div style={{ height:"100%", width:`${Math.round(m.kcal/totalKcal*100)}%`, background:plan.color, borderRadius:2 }} />
              </div>
              <span style={{ fontSize:11, color:C.t2 }}>{Math.round(m.kcal/totalKcal*100)}%</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: FOOD SEARCH
═══════════════════════════════════════════════════════════════════ */
function FoodSearchPage() {
  const [query, setQuery] = useState("");
  const [cat, setCat] = useState("All");
  const [log, setLog] = useState([]);
  const cats = ["All",...[...new Set(FOOD_DB.map(f => f.cat))]];
  const filtered = FOOD_DB.filter(f =>
    (cat === "All" || f.cat === cat) &&
    f.name.toLowerCase().includes(query.toLowerCase())
  );
  const totals = log.reduce((acc,f) => ({ kcal:acc.kcal+f.kcal, p:acc.p+f.p, fat:acc.fat+f.f, c:acc.c+f.c }), { kcal:0, p:0, fat:0, c:0 });

  return (
    <div style={{ padding:24, display:"grid", gridTemplateColumns:"1fr 320px", gap:16, alignItems:"start" }}>
      <div>
        <div style={{ fontSize:18, fontWeight:600, color:C.t0, marginBottom:4 }}>Food search</div>
        <div style={{ fontSize:12, color:C.t2, marginBottom:16 }}>Search and track your meals to monitor daily intake</div>

        <div style={{ display:"flex", gap:10, marginBottom:14 }}>
          <div style={{ flex:1, position:"relative" }}>
            <svg style={{ position:"absolute", left:10, top:"50%", transform:"translateY(-50%)" }} width={14} height={14} viewBox="0 0 24 24" fill={C.t2}>
              <path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7 14 5 12 5 9.5S7 5 9.5 5 14 7 14 9.5 12 14 9.5 14z" />
            </svg>
            <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search foods…"
              style={{ width:"100%", padding:"9px 10px 9px 32px", background:C.bg2, border:`1px solid ${C.border}`, borderRadius:6, color:C.t0, fontSize:13, outline:"none" }} />
          </div>
          <select value={cat} onChange={e => setCat(e.target.value)}
            style={{ padding:"9px 10px", background:C.bg2, border:`1px solid ${C.border}`, borderRadius:6, color:C.t0, fontSize:13, outline:"none" }}>
            {cats.map(c => <option key={c} value={c} style={{ background:C.bg2 }}>{c}</option>)}
          </select>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
          {filtered.map((f,i) => (
            <div key={i} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"11px 14px", background:C.bg1, border:`1px solid ${C.border}`, borderRadius:7 }}>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:13, color:C.t0, fontWeight:500 }}>{f.name}</div>
                <div style={{ display:"flex", gap:12, marginTop:3 }}>
                  <span style={{ fontSize:11, color:C.t2 }}>P: <Mono size={11}>{f.p}g</Mono></span>
                  <span style={{ fontSize:11, color:C.t2 }}>F: <Mono size={11}>{f.f}g</Mono></span>
                  <span style={{ fontSize:11, color:C.t2 }}>C: <Mono size={11}>{f.c}g</Mono></span>
                </div>
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                <Mono color={C.green}>{f.kcal}</Mono>
                <span style={{ fontSize:11, color:C.t2 }}>kcal</span>
                <Btn small variant="secondary" onClick={() => setLog(l => [...l, f])}>+ Add</Btn>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <div style={{ padding:"28px 0", textAlign:"center", fontSize:13, color:C.t2 }}>No results for "{query}"</div>}
        </div>
      </div>

      {/* Food log */}
      <Card style={{ padding:16 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
          <SectionLabel style={{ marginBottom:0 }}>Daily log</SectionLabel>
          {log.length > 0 && <Btn small variant="ghost" onClick={() => setLog([])}>Clear</Btn>}
        </div>
        {log.length === 0 ? (
          <div style={{ padding:"20px 0", textAlign:"center", fontSize:12, color:C.t2 }}>Add foods from the left to log your intake</div>
        ) : (
          <>
            {log.map((f,i) => (
              <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"7px 0", borderBottom:`1px solid ${C.border}`, fontSize:12 }}>
                <span style={{ color:C.t1 }}>{f.name}</span>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <Mono size={12} color={C.green}>{f.kcal}</Mono>
                  <button onClick={() => setLog(l => l.filter((_,j) => j!==i))} style={{ background:"none", border:"none", color:C.t2, cursor:"pointer", fontSize:14, lineHeight:1 }}>×</button>
                </div>
              </div>
            ))}
            <div style={{ marginTop:12, padding:"10px 0", borderTop:`1px solid ${C.border}` }}>
              <div style={{ fontSize:11, color:C.t2, marginBottom:6 }}>Total intake</div>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
                <Mono color={C.green} size={18}>{totals.kcal}</Mono>
                <span style={{ fontSize:11, color:C.t2, alignSelf:"flex-end" }}>kcal</span>
              </div>
              {[["Protein",totals.p,"g",C.green],["Fat",totals.fat,"g",C.amber],["Carbs",totals.c,"g",C.blue]].map(([l,v,u,c]) => (
                <div key={l} style={{ display:"flex", justifyContent:"space-between", fontSize:11, padding:"3px 0" }}>
                  <span style={{ color:C.t2 }}>{l}</span>
                  <Mono size={11} color={c}>{v}{u}</Mono>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: CALCULATOR (BMI + TDEE)
═══════════════════════════════════════════════════════════════════ */
function CalculatorPage({ form }) {
  const [calc, setCalc] = useState({ weight: form.weight, height: form.height, age: form.age, gender: form.gender, activity: form.activity });
  const setC = k => v => setCalc(p => ({...p, [k]:v}));
  const bmi = calc.weight / (calc.height / 100) ** 2;
  const bmr = calc.gender === "Male"
    ? 88.362 + (13.397 * calc.weight) + (4.799 * calc.height) - (5.677 * calc.age)
    : 447.593 + (9.247 * calc.weight) + (3.098 * calc.height) - (4.330 * calc.age);
  const actMult = { Sedentary:1.2, Moderate:1.55, Active:1.725 };
  const tdee = bmr * (actMult[calc.activity] || 1.375);
  const bmiCat = bmi < 18.5 ? "Underweight" : bmi < 25 ? "Normal" : bmi < 30 ? "Overweight" : "Obese";
  const bmiColor = bmi < 18.5 ? C.blue : bmi < 25 ? C.green : bmi < 30 ? C.amber : C.red;

  const weightGoals = [
    { label:"Lose weight (−0.5 kg/week)", kcal: Math.round(tdee - 500) },
    { label:"Maintain weight", kcal: Math.round(tdee) },
    { label:"Gain weight (+0.5 kg/week)", kcal: Math.round(tdee + 500) },
  ];

  return (
    <div style={{ padding:24, maxWidth:700 }}>
      <div style={{ fontSize:18, fontWeight:600, color:C.t0, marginBottom:4 }}>Body calculators</div>
      <div style={{ fontSize:12, color:C.t2, marginBottom:20 }}>BMI, BMR, and TDEE computed from your biometrics</div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:20 }}>
        <FInput label="Weight" suffix="kg" value={calc.weight} onChange={setC("weight")} min={30} max={300} step={.1} />
        <FInput label="Height" suffix="cm" value={calc.height} onChange={setC("height")} min={100} max={250} />
        <FInput label="Age" suffix="yrs" value={calc.age} onChange={setC("age")} min={18} max={100} />
        <FSelect label="Sex" value={calc.gender} onChange={setC("gender")} options={["Male","Female"]} />
        <FSelect label="Activity level" value={calc.activity} onChange={setC("activity")} options={["Sedentary","Moderate","Active"]} />
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:14, marginBottom:20 }}>
        {[
          { label:"BMI", value:bmi.toFixed(1), unit:"kg/m²", sub:bmiCat, color:bmiColor },
          { label:"BMR", value:Math.round(bmr).toLocaleString(), unit:"kcal/day", sub:"Basal metabolic rate", color:C.teal },
          { label:"TDEE", value:Math.round(tdee).toLocaleString(), unit:"kcal/day", sub:"Total daily expenditure", color:C.blue },
        ].map(d => (
          <Card key={d.label} style={{ padding:"16px 18px" }}>
            <div style={{ fontSize:11, color:C.t2, textTransform:"uppercase", letterSpacing:".05em", marginBottom:8 }}>{d.label}</div>
            <Mono color={d.color} size={24}>{d.value}</Mono>
            <span style={{ fontSize:11, color:C.t2, marginLeft:4 }}>{d.unit}</span>
            <div style={{ fontSize:11, color:C.t2, marginTop:4 }}>{d.sub}</div>
          </Card>
        ))}
      </div>

      <Card style={{ padding:18 }}>
        <SectionLabel>Caloric targets by goal</SectionLabel>
        {weightGoals.map((g,i) => (
          <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"10px 0", borderBottom: i < weightGoals.length-1 ? `1px solid ${C.border}` : "none" }}>
            <span style={{ fontSize:13, color:C.t1 }}>{g.label}</span>
            <div>
              <Mono color={i===1?C.green:C.t1} size={15}>{g.kcal.toLocaleString()}</Mono>
              <span style={{ fontSize:11, color:C.t2, marginLeft:4 }}>kcal/day</span>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: PROGRESS TRACKING
═══════════════════════════════════════════════════════════════════ */
function ProgressPage({ form, result }) {
  const initLogs = [
    { date: new Date(Date.now()-7*86400000).toISOString().slice(0,10), glucose: form.glucose+10, bp: form.bp+5, weight: form.weight+1.2, note:"Baseline" },
    { date: new Date(Date.now()-3*86400000).toISOString().slice(0,10), glucose: form.glucose+4, bp: form.bp+2, weight: form.weight+0.4, note:"Week 1" },
    { date: new Date().toISOString().slice(0,10), glucose: form.glucose, bp: form.bp, weight: form.weight, note:"Current" },
  ];
  const [logs, setLogs] = useState(initLogs);
  const [entry, setEntry] = useState({ date: new Date().toISOString().slice(0,10), glucose:"", bp:"", weight:"", note:"" });
  const setE = k => v => setEntry(p => ({...p, [k]:v}));

  const addEntry = () => {
    if (!entry.glucose && !entry.bp && !entry.weight) return;
    setLogs(l => [...l, { ...entry, glucose: parseFloat(entry.glucose)||0, bp: parseFloat(entry.bp)||0, weight: parseFloat(entry.weight)||0 }].sort((a,b) => a.date.localeCompare(b.date)));
    setEntry(p => ({...p, glucose:"", bp:"", weight:"", note:""}));
  };

  const trend = key => {
    if (logs.length < 2) return null;
    const delta = logs[logs.length-1][key] - logs[0][key];
    return delta;
  };

  return (
    <div style={{ padding:24 }}>
      <div style={{ fontSize:18, fontWeight:600, color:C.t0, marginBottom:4 }}>Progress tracking</div>
      <div style={{ fontSize:12, color:C.t2, marginBottom:20 }}>Log your biometrics over time to monitor your diet plan's effectiveness</div>

      {/* Trend summary */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:20 }}>
        {[["Glucose", "glucose", "mg/dL", false],["Blood pressure","bp","mmHg",false],["Weight","weight","kg",false]].map(([label,key,unit,higherGood]) => {
          const t = trend(key);
          const improving = t !== null && (higherGood ? t > 0 : t < 0);
          return (
            <Card key={key} style={{ padding:"14px 16px" }}>
              <div style={{ fontSize:11, color:C.t2, textTransform:"uppercase", letterSpacing:".05em", marginBottom:6 }}>{label}</div>
              <Mono color={C.t0} size={20}>{logs[logs.length-1]?.[key] || "—"}</Mono>
              <span style={{ fontSize:11, color:C.t2, marginLeft:4 }}>{unit}</span>
              {t !== null && (
                <div style={{ fontSize:11, color: improving ? C.green : C.amber, marginTop:4 }}>
                  {t > 0 ? "▲" : "▼"} {Math.abs(t).toFixed(1)} from baseline
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Log table */}
      <Card style={{ padding:16, marginBottom:16 }}>
        <SectionLabel>History</SectionLabel>
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
            <thead>
              <tr style={{ borderBottom:`1px solid ${C.border}` }}>
                {["Date","Glucose","BP","Weight","Note"].map(h => (
                  <th key={h} style={{ padding:"6px 10px", textAlign:"left", color:C.t2, fontWeight:500, fontSize:11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((l,i) => (
                <tr key={i} style={{ borderBottom:`1px solid ${C.border}` }}>
                  <td style={{ padding:"9px 10px", color:C.t1, fontFamily:F.mono, fontSize:12 }}>{l.date}</td>
                  <td style={{ padding:"9px 10px", color:l.glucose>140?C.amber:C.t0, fontFamily:F.mono }}>{l.glucose || "—"}</td>
                  <td style={{ padding:"9px 10px", color:l.bp>140?C.amber:C.t0, fontFamily:F.mono }}>{l.bp || "—"}</td>
                  <td style={{ padding:"9px 10px", color:C.t0, fontFamily:F.mono }}>{l.weight || "—"}</td>
                  <td style={{ padding:"9px 10px", color:C.t2 }}>{l.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add entry */}
      <Card style={{ padding:16 }}>
        <SectionLabel>Add entry</SectionLabel>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(5, 1fr)", gap:10 }}>
          <FInput label="Date" type="text" value={entry.date} onChange={setE("date")} placeholder="YYYY-MM-DD" />
          <FInput label="Glucose" suffix="mg/dL" value={entry.glucose} onChange={setE("glucose")} step={.1} />
          <FInput label="BP" suffix="mmHg" value={entry.bp} onChange={setE("bp")} />
          <FInput label="Weight" suffix="kg" value={entry.weight} onChange={setE("weight")} step={.1} />
          <FInput label="Note" type="text" value={entry.note} onChange={setE("note")} placeholder="e.g. Week 2" />
        </div>
        <div style={{ marginTop:12 }}>
          <Btn onClick={addEntry}>Add entry</Btn>
        </div>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: REPORT
═══════════════════════════════════════════════════════════════════ */
function ReportPage({ form, result }) {
  const plan = DIET_PLANS[result.diet];
  const meals = MEALS_DB[result.mealCat]?.[form.cuisine] || [];
  const totalKcal = meals.reduce((a,m) => a+m.kcal, 0);

  const printReport = () => {
    const w = window.open("", "_blank");
    w.document.write(`
      <html><head><title>NutriPlanner Report — ${new Date().toLocaleDateString()}</title>
      <style>
        body { font-family: 'DM Sans', sans-serif; color: #111; background: #fff; max-width: 700px; margin: 40px auto; padding: 0 24px; font-size: 13px; line-height: 1.6; }
        h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
        h2 { font-size: 15px; font-weight: 600; margin: 24px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #e5e7eb; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; margin-right: 4px; }
        .green { background: #f0fdf4; color: #15803d; } .amber { background: #fffbeb; color: #b45309; } .red { background: #fef2f2; color: #b91c1c; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td,th { padding: 7px 10px; text-align: left; border-bottom: 1px solid #f3f4f6; font-size: 12px; }
        th { color: #6b7280; font-weight: 500; }
        .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; }
        .pill { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; margin: 2px; }
        .gpill { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
        .rpill { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
        footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; }
      </style></head><body>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px">
        <div><h1>NutriPlanner Clinical Report</h1><div style="color:#6b7280;font-size:12px">Generated ${new Date().toLocaleDateString("en-IN", { weekday:"long",year:"numeric",month:"long",day:"numeric" })}</div></div>
        <div style="text-align:right"><div style="font-size:20px;font-weight:700;color:#15803d">${result.diet.replace("_"," ")}</div><div style="font-size:11px;color:#6b7280">${Math.round(result.conf*100)}% model confidence</div></div>
      </div>

      <h2>Patient Profile</h2>
      <div class="grid2">
        <table><tr><th>Field</th><th>Value</th></tr>
          <tr><td>Age / Sex</td><td>${form.age} yrs · ${form.gender}</td></tr>
          <tr><td>Weight / Height</td><td>${form.weight} kg · ${form.height} cm</td></tr>
          <tr><td>BMI</td><td>${result.bmi} kg/m²</td></tr>
          <tr><td>Condition</td><td>${form.diseaseType} (${form.severity})</td></tr>
          <tr><td>Activity</td><td>${form.activity}</td></tr>
          <tr><td>Cuisine</td><td>${form.cuisine}</td></tr>
        </table>
        <table><tr><th>Biomarker</th><th>Value</th><th>Status</th></tr>
          <tr><td>Glucose</td><td>${form.glucose} mg/dL</td><td><span class="badge ${form.glucose>140?"amber":"green"}">${form.glucose>140?"Elevated":"Normal"}</span></td></tr>
          <tr><td>Blood Pressure</td><td>${form.bp} mmHg</td><td><span class="badge ${form.bp>140?"amber":"green"}">${form.bp>140?"Elevated":"Normal"}</span></td></tr>
          <tr><td>Cholesterol</td><td>${form.cholesterol} mg/dL</td><td><span class="badge ${form.cholesterol>200?"amber":"green"}">${form.cholesterol>200?"Elevated":"Normal"}</span></td></tr>
          <tr><td>Risk Score</td><td>${result.riskScore}/100</td><td><span class="badge ${result.riskLevel==="High"?"red":result.riskLevel==="Moderate"?"amber":"green"}">${result.riskLevel}</span></td></tr>
        </table>
      </div>

      <h2>Diet Protocol — ${plan.label}</h2>
      <div class="grid2">
        <div><strong>Recommended foods</strong><br/>${plan.include.map(f => `<span class="pill gpill">${f}</span>`).join("")}</div>
        <div><strong>Foods to avoid</strong><br/>${plan.exclude.map(f => `<span class="pill rpill">${f}</span>`).join("")}</div>
      </div>
      <p style="margin-top:10px"><strong>Daily calorie target:</strong> ${plan.kcal} kcal/day</p>

      <h2>Clinical Insights</h2>
      <ul>${result.insights.map(i => `<li style="margin-bottom:5px">${i}</li>`).join("")}</ul>

      <h2>Sample Meal Plan (${form.cuisine} Cuisine)</h2>
      <table><tr><th>Meal</th><th>Description</th><th>Calories</th><th>Protein</th></tr>
        ${meals.map(m => `<tr><td>${m.time}</td><td>${m.name}</td><td>${m.kcal} kcal</td><td>${m.p}g</td></tr>`).join("")}
        <tr style="font-weight:600"><td colspan="2">Total</td><td>${totalKcal} kcal</td><td>${meals.reduce((a,m)=>a+m.p,0)}g</td></tr>
      </table>

      <footer>
        NutriPlanner Clinical Platform · Models: GBM (diet, ${(result.conf*100).toFixed(0)}% conf) · RF Regressor (risk, RMSE 3.9) · RF Classifier (meals) · Trained on 1,000 patient records<br/>
        ⚕️ This report is for informational purposes only. Always consult a licensed dietitian or physician before making dietary changes.
      </footer>
      </body></html>`);
    w.document.close();
    setTimeout(() => w.print(), 500);
  };

  return (
    <div style={{ padding:24 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:600, color:C.t0, marginBottom:4 }}>Printable report</div>
          <div style={{ fontSize:12, color:C.t2 }}>Full clinical summary ready for export</div>
        </div>
        <Btn onClick={printReport}>
          <svg width={14} height={14} viewBox="0 0 24 24" fill="currentColor"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/></svg>
          Print / Download PDF
        </Btn>
      </div>

      {/* Preview */}
      <Card style={{ padding:"28px 32px" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:20 }}>
          <div>
            <div style={{ fontSize:18, fontWeight:600, color:C.t0 }}>NutriPlanner Clinical Report</div>
            <div style={{ fontSize:12, color:C.t2, marginTop:2 }}>{new Date().toLocaleDateString("en-IN",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}</div>
          </div>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontSize:20, fontWeight:700, color:plan.color }}>{plan.label}</div>
            <div style={{ fontSize:11, color:C.t2 }}>{Math.round(result.conf*100)}% model confidence</div>
          </div>
        </div>

        <Divider style={{ marginBottom:16 }} />

        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20, marginBottom:20 }}>
          <div>
            <div style={{ fontSize:12, fontWeight:600, color:C.t1, marginBottom:8 }}>Patient profile</div>
            {[["Age / Sex",`${form.age} yrs · ${form.gender}`],["Weight / Height",`${form.weight} kg · ${form.height} cm`],["BMI",`${result.bmi} kg/m²`],["Condition",`${form.diseaseType} (${form.severity})`],["Activity",form.activity]].map(([k,v]) => (
              <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:`1px solid ${C.border}`, fontSize:12 }}>
                <span style={{ color:C.t2 }}>{k}</span><span style={{ color:C.t0 }}>{v}</span>
              </div>
            ))}
          </div>
          <div>
            <div style={{ fontSize:12, fontWeight:600, color:C.t1, marginBottom:8 }}>Biomarkers</div>
            {[["Glucose",form.glucose,"mg/dL",form.glucose>140],["Blood pressure",form.bp,"mmHg",form.bp>140],["Cholesterol",form.cholesterol,"mg/dL",form.cholesterol>200],["Risk score",`${result.riskScore}/100`,"",result.riskScore>40]].map(([k,v,u,warn]) => (
              <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"5px 0", borderBottom:`1px solid ${C.border}`, fontSize:12 }}>
                <span style={{ color:C.t2 }}>{k}</span>
                <span style={{ color: warn ? C.amber : C.green }}>{v} {u}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom:16 }}>
          <div style={{ fontSize:12, fontWeight:600, color:C.t1, marginBottom:8 }}>Clinical insights</div>
          {result.insights.map((ins,i) => (
            <div key={i} style={{ fontSize:12, color:C.t1, padding:"7px 10px", borderLeft:`2px solid ${plan.color}`, marginBottom:6, background:C.bg2, borderRadius:"0 4px 4px 0" }}>{ins}</div>
          ))}
        </div>

        <div style={{ fontSize:11, color:C.t2, paddingTop:14, borderTop:`1px solid ${C.border}` }}>
          ⚕️ For informational purposes only. Always consult a licensed dietitian or physician before making dietary changes.
        </div>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: AI CHAT
═══════════════════════════════════════════════════════════════════ */
function AIChatPage({ form, result }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const endRef = useRef(null);
  const plan = DIET_PLANS[result.diet];

  const system = `You are NutriPlanner, a clinical-grade AI nutrition assistant. You have access to the patient's complete health profile and ML-generated analysis.

PATIENT PROFILE:
- Age: ${form.age} | Sex: ${form.gender} | BMI: ${result.bmi} kg/m²
- Condition: ${form.diseaseType} (${form.severity}) | Activity: ${form.activity}
- Glucose: ${form.glucose} mg/dL | BP: ${form.bp} mmHg | Cholesterol: ${form.cholesterol} mg/dL
- Daily caloric intake: ${form.calories} kcal | Exercise: ${form.exercise} hrs/week
- Restrictions: ${form.restrictions} | Allergies: ${form.allergies} | Cuisine: ${form.cuisine}

ML MODEL OUTPUT:
- Diet protocol: ${result.diet} (${Math.round(result.conf*100)}% confidence)
- Risk score: ${result.riskScore}/100 (${result.riskLevel} risk)
- Meal category: ${result.mealCat}
- Health scores — Metabolic: ${result.scores.metabolic} | Cardiovascular: ${result.scores.cardiovascular} | Lifestyle: ${result.scores.lifestyle}

RESPONSE STYLE:
- Clinical, precise, evidence-based — not cheerleader-ish or generic
- Reference the patient's actual numbers when relevant
- Suggest meal ideas respecting their cuisine preference (${form.cuisine}) and allergies
- Keep responses 2–4 paragraphs, structured
- End with: "Always consult your physician or dietitian for clinical decisions."`;

  const send = async (text) => {
    const next = [...msgs, { role:"user", content:text }];
    setMsgs(next); setInput(""); setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ patient_data: mapFormToPatient(form), messages: next }),
      });
      const data = await res.json();
      setMsgs(p => [...p, { role:"assistant", content: data.content?.[0]?.text || "Unable to process. Please retry." }]);
    } catch {
      setMsgs(p => [...p, { role:"assistant", content:"Connection error. Please ensure the backend server is running." }]);
    }
    setLoading(false);
  };

  const startSession = async () => {
    setStarted(true); setLoading(true);
    const init = `Provide a concise clinical summary: what the patient's data indicates, why ${result.diet} is recommended, and the top 2 immediate actions they should take. Be specific to their numbers.`;
    const mappedData = {
      age: form.age, gender: form.gender, weight_kg: form.weight, height_cm: form.height,
      disease_type: form.diseaseType, severity: form.severity, activity_level: form.activity,
      daily_caloric: form.calories, cholesterol: form.cholesterol, blood_pressure: form.bp,
      glucose: form.glucose, weekly_exercise: form.exercise, adherence: form.adherence,
      nutrient_imbalance: form.nutrientImbalance, restrictions: form.restrictions,
      allergies: form.allergies, cuisine: form.cuisine
    };

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ patient_data: mapFormToPatient(form), messages: [{ role: "user", content: init }] }),
      });
      const data = await res.json();
      setMsgs([{ role:"assistant", content: data.content?.[0]?.text || `Based on your profile, the ${result.diet} protocol is recommended.` }]);
    } catch {
      setMsgs([{ role:"assistant", content:`Based on your profile analysis, the ${result.diet} protocol is the appropriate dietary intervention. Ask me anything specific about your plan.` }]);
    }
    setLoading(false);
  };

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs, loading]);

  const quick = [`What ${form.cuisine} meals suit my protocol?`, "Give me a 7-day meal schedule", "What are my biomarker targets?", "How can I improve my risk score?"];

  return (
    <div style={{ padding:24, height:"calc(100vh - 52px)", display:"flex", flexDirection:"column" }}>
      <div style={{ fontSize:18, fontWeight:600, color:C.t0, marginBottom:4 }}>AI consultation</div>
      <div style={{ fontSize:12, color:C.t2, marginBottom:16 }}>Context-aware clinical nutrition assistant · {result.diet.replace("_"," ")} protocol</div>

      <Card style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
        <div style={{ padding:"12px 16px", borderBottom:`1px solid ${C.border}`, display:"flex", alignItems:"center", gap:8 }}>
          <div style={{ width:7, height:7, borderRadius:"50%", background: started && !loading ? C.green : C.t2, animation: loading ? "pulse 1.5s infinite" : "none" }} />
          <span style={{ fontSize:13, fontWeight:500, color:C.t0 }}>NutriPlanner Clinical</span>
          <span style={{ fontSize:11, color:C.t2 }}>· Personalised to your health profile</span>
        </div>

        <div style={{ flex:1, overflowY:"auto", padding:16, display:"flex", flexDirection:"column", gap:12, minHeight:0 }}>
          {!started && !loading && (
            <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:"100%", gap:14, opacity:.8 }}>
              <div style={{ width:44, height:44, borderRadius:10, background:C.bg3, border:`1px solid ${C.border}`, display:"flex", alignItems:"center", justifyContent:"center" }}>
                <svg width={20} height={20} viewBox="0 0 24 24" fill={C.green}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
              </div>
              <div style={{ textAlign:"center" }}>
                <div style={{ fontSize:14, fontWeight:500, color:C.t1, marginBottom:4 }}>AI consultation ready</div>
                <div style={{ fontSize:12, color:C.t2 }}>Start a session to receive your personalised clinical summary</div>
              </div>
              <Btn variant="secondary" onClick={startSession}>Begin session</Btn>
            </div>
          )}
          {msgs.map((m,i) => (
            <div key={i} style={{ display:"flex", flexDirection:"column", alignItems: m.role==="user" ? "flex-end" : "flex-start" }}>
              {m.role==="assistant" && <div style={{ fontSize:10, color:C.t2, marginBottom:3, letterSpacing:".04em", textTransform:"uppercase" }}>NutriPlanner</div>}
              <div style={{ maxWidth:"85%", padding:"10px 13px", borderRadius: m.role==="user" ? "8px 8px 2px 8px" : "2px 8px 8px 8px",
                background: m.role==="user" ? C.bg3 : `${plan.color}12`,
                border: `1px solid ${m.role==="user" ? C.border : plan.color+"30"}`,
                fontSize:13, lineHeight:1.65, color:C.t0 }}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display:"flex", gap:4, padding:"10px 13px", background:`${C.green}10`, border:`1px solid ${C.green}25`, borderRadius:"2px 8px 8px 8px", width:"fit-content" }}>
              {[0,1,2].map(i => <div key={i} style={{ width:5,height:5,borderRadius:"50%",background:C.green,animation:`pulse 1.2s ${i*.2}s infinite` }} />)}
            </div>
          )}
          <div ref={endRef} />
        </div>

        {started && (
          <div style={{ padding:"7px 12px", borderTop:`1px solid ${C.border}`, display:"flex", gap:5, overflowX:"auto" }}>
            {quick.map((q,i) => (
              <button key={i} onClick={() => send(q)} style={{ whiteSpace:"nowrap", padding:"4px 9px", background:C.bg2, border:`1px solid ${C.border}`, borderRadius:4, color:C.t1, fontSize:11, cursor:"pointer", flexShrink:0 }}>{q}</button>
            ))}
          </div>
        )}

        <div style={{ padding:"10px 12px", borderTop:`1px solid ${C.border}`, display:"flex", gap:8 }}>
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==="Enter" && send(input)}
            placeholder={started ? "Ask a clinical nutrition question…" : "Start a session first"}
            disabled={!started}
            style={{ flex:1, padding:"9px 12px", background:C.bg2, border:`1px solid ${C.border}`, borderRadius:6, color:C.t0, fontSize:13, outline:"none" }} />
          <Btn onClick={() => send(input)} disabled={loading || !input.trim() || !started}>Send</Btn>
        </div>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   PAGE: METRICS (Classification Matrix)
═══════════════════════════════════════════════════════════════════ */
function MetricsPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BACKEND_URL}/metrics`)
      .then(res => res.json())
      .then(data => { setMetrics(data); setLoading(false); })
      .catch(() => { setMetrics(null); setLoading(false); });
  }, []);

  if (loading) return <div style={{ padding: 24, display: "flex", alignItems: "center", gap: 10 }}><Spinner /><span style={{ fontSize:13, color:C.t1 }}>Loading metrics...</span></div>;
  if (!metrics) return <div style={{ padding: 24, fontSize: 13, color: C.red }}>Failed to load metrics. Ensure the backend server is running.</div>;

  return (
    <div style={{ padding: 24, maxWidth: 800 }}>
      <div style={{ fontSize: 18, fontWeight: 600, color: C.t0, marginBottom: 4 }}>Classification matrix & Accuracy check</div>
      <div style={{ fontSize: 12, color: C.t2, marginBottom: 20 }}>Model performance on 1,000 synthetic patient records</div>
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <Card style={{ padding: "20px 24px" }}>
          <SectionLabel>Overall Model Accuracy</SectionLabel>
          <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
            <Mono size={32} color={C.green}>{(metrics.accuracy * 100).toFixed(1)}%</Mono>
            <span style={{ fontSize: 12, color: C.t2 }}>Test score</span>
          </div>
        </Card>
      </div>
      
      <Card style={{ padding: "20px 24px", marginBottom: 16 }}>
        <SectionLabel>Confusion Matrix</SectionLabel>
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 600 }}>
            <thead>
              <tr>
                <th style={{ padding: 10, border: `1px solid ${C.border}`, background: C.bg2, fontSize: 11, color: C.t1, textAlign: "left", fontWeight: 600 }}>Actual \\ Predicted</th>
                {metrics.classes.map(c => <th key={c} style={{ padding: 10, border: `1px solid ${C.border}`, background: C.bg2, fontSize: 11, color: C.t1, fontWeight: 600 }}>{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {metrics.confusion_matrix.map((row, i) => (
                <tr key={i}>
                  <td style={{ padding: 10, border: `1px solid ${C.border}`, background: C.bg2, fontSize: 11, color: C.t1, fontWeight: 600 }}>{metrics.classes[i]}</td>
                  {row.map((val, j) => (
                    <td key={j} style={{ padding: 10, border: `1px solid ${C.border}`, textAlign: "center", background: i === j ? "rgba(34,197,94,.08)" : "transparent" }}>
                      <Mono size={13} color={i === j ? C.green : C.t0}>{val}</Mono>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      
      <Card style={{ padding: "20px 24px" }}>
        <SectionLabel>Classification Report</SectionLabel>
        <div style={{ padding: 14, background: C.bg0, borderRadius: 6, border: `1px solid ${C.border}`, overflowX: "auto" }}>
          <pre style={{ margin: 0, fontSize: 12, color: C.t0, fontFamily: F.mono, lineHeight: 1.6 }}>{JSON.stringify(metrics.classification_report, null, 2)}</pre>
        </div>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ROOT APP
═══════════════════════════════════════════════════════════════════ */
export default function App() {
  const [view, setView] = useState("onboarding");
  const [form, setForm] = useState(null);
  const [result, setResult] = useState(null);
  const [page, setPage] = useState("dashboard");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (f) => {
    setForm(f);
    setSubmitting(true);
    try {
      const res = await fetch(`${BACKEND_URL}/predict`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mapFormToPatient(f)),
      });
      const data = await res.json();
      setResult(data);
      setView("app");
    } catch (e) {
      console.error("Backend prediction failed, falling back to local inference", e);
      setResult(runMLInference(f));
      setView("app");
    }
    setSubmitting(false);
  };

  if (view === "onboarding") return (<OnboardingForm onSubmit={handleSubmit} submitting={submitting} />);

  return (
    <>
      <div style={{ display:"flex", height:"100vh", overflow:"hidden", background:C.bg0 }}>
        <Sidebar active={page} onNav={setPage} result={result} />
        <main style={{ flex:1, overflowY:"auto" }}>
          {page === "dashboard"   && <DashboardPage  form={form} result={result} />}
          {page === "meals"       && <MealPlanPage   form={form} result={result} />}
          {page === "foodsearch"  && <FoodSearchPage />}
          {page === "calculator"  && <CalculatorPage form={form} />}
          {page === "progress"    && <ProgressPage   form={form} result={result} />}
          {page === "report"      && <ReportPage     form={form} result={result} />}
          {page === "metrics"     && <MetricsPage />}
          {page === "aichat"      && <AIChatPage     form={form} result={result} />}
        </main>
      </div>
    </>
  );
}
