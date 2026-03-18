"""
NutriGuard AI — Streamlit Cloud Entry Point
============================================
Run locally :  streamlit run app.py
Deploy      :  push to GitHub → connect on share.streamlit.io
"""

import json
import os
from typing import Any, Dict, List, Tuple

import streamlit as st

# ── Optional: load .env when running locally ──────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Google Gemini (optional — graceful fallback if key absent) ─────────────────
try:
    from google import genai as _genai_module
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    _genai_module = None  # type: ignore

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE LOGIC  (same algorithms used by the FastAPI backend)
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m ** 2), 1)


def _classify_bmi(bmi: float) -> str:
    if bmi <= 0:        return "غير معروف"
    if bmi < 18.5:      return "نقص في الوزن"
    if bmi < 25:        return "وزن طبيعي"
    if bmi < 30:        return "زيادة في الوزن"
    return "سمنة"


def _estimate_daily_calories(weight_kg: float, age: int) -> int:
    factor = 24 if age < 40 else 22 if age < 60 else 20
    return int(weight_kg * factor)


def _parse_ai_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned)


def _gemini_plan(bmi: float, bmi_status: str,
                 daily_calories: int, chronic_disease: str) -> Dict[str, Any] | None:
    if not (_GEMINI_AVAILABLE and _GEMINI_API_KEY):
        return None
    prompt = (
        "أنت اختصاصي تغذية ذكي. استخدم المعلومات التالية عن المستخدم:\n"
        f"- مؤشر كتلة الجسم (BMI): {bmi}، الحالة: {bmi_status}\n"
        f"- الاحتياج التقريبي اليومي من السعرات: {daily_calories}\n"
        f"- المرض المزمن: {chronic_disease}\n\n"
        "أعد خطة غذائية مبسّطة باللغة العربية فقط في شكل JSON خالص بدون نص إضافي.\n"
        "يجب أن يحتوي كائن JSON الناتج بالضرورة على المفاتيح التالية بالضبط لهذه القوائم:\n"
        '- "recommended_foods": قائمة من 4 إلى 6 أطعمة موصى بها،\n'
        '- "forbidden_foods": قائمة من 3 إلى 5 أطعمة يجب تجنبها،\n'
        '- "health_habits": قائمة من 3 إلى 5 عادات ونصائح عملية يومية.\n'
        "يمكنك أيضًا إضافة المفتاحين التاليين:\n"
        '- "risk_level": قيمة نصية مثل "منخفض" أو "متوسط" أو "مرتفع"،\n'
        '- "message": رسالة تشجيعية لطيفة ومساندة تلخّص الحالة والنصائح.\n\n'
        "أعد الرد على شكل JSON فقط بدون أي نص خارجه، وبالعربية في جميع القيم."
    )
    try:
        client = _genai_module.Client(api_key=_GEMINI_API_KEY)  # type: ignore[union-attr]
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )
        return _parse_ai_json(response.text or "")
    except Exception:
        return None


def _fallback_plan(chronic_disease: str,
                   bmi_status: str) -> Tuple[List[str], List[str], List[str], str, str]:
    disease = chronic_disease.lower()

    if "diab" in disease or "سكر" in disease:
        recommended = ["خضروات ورقية داكنة", "حبوب كاملة مثل الشوفان",
                       "عدس وبقوليات", "بروتينات خفيفة مثل الدجاج المشوي", "مكسرات غير مملحة"]
        forbidden  = ["مشروبات غازية محلاة", "حلويات بكثرة السكر", "خبز أبيض وأرز أبيض"]
        habits     = ["المشي 30 دقيقة يوميًا بعد الوجبات",
                      "توزيع الكربوهيدرات على وجبات صغيرة",
                      "قياس سكر الدم بانتظام بالتنسيق مع الطبيب"]
        risk, label = "متوسط", "السكري"

    elif "hyper" in disease or "ضغط" in disease:
        recommended = ["خضروات طازجة متنوعة", "أطعمة قليلة الملح",
                       "زيت الزيتون كبديل للدهون الصلبة", "فواكه غنية بالبوتاسيوم مثل الموز", "أسماك مشوية"]
        forbidden  = ["أطعمة معلبة عالية الصوديوم", "وجبات سريعة", "مخللات كثيرة الملح"]
        habits     = ["قياس ضغط الدم بانتظام", "تقليل إضافة الملح على المائدة",
                      "ممارسة نشاط بدني معتدل 5 أيام في الأسبوع"]
        risk, label = "متوسط", "ارتفاع ضغط الدم"

    elif "chol" in disease or "دهون" in disease or "كوليسترول" in disease:
        recommended = ["أسماك دهنية صحية مثل السلمون", "مكسرات غير مملحة",
                       "حبوب كاملة مثل الشوفان والشعير", "أطعمة غنية بالألياف مثل التفاح", "زيت الزيتون والأفوكادو"]
        forbidden  = ["أطعمة مقلية", "دهون مشبعة مثل السمن الصناعي", "لحوم مصنّعة"]
        habits     = ["استبدال القلي بالشوي أو السلق", "الحد من صفار البيض واللحوم الدسمة",
                      "إدخال تمارين هوائية خفيفة بانتظام"]
        risk, label = "مرتفع", "ارتفاع الكوليسترول"

    else:
        recommended = ["خضروات موسمية متنوعة", "فواكه طازجة بكميات معتدلة",
                       "ماء كافٍ على مدار اليوم", "بروتين متوازن من مصادر مختلفة", "حبوب كاملة بدلًا من المكررة"]
        forbidden  = ["مشروبات محلاة بشكل متكرر", "مقالي متكررة", "وجبات سريعة غنية بالدهون"]
        habits     = ["المشي أو الحركة الخفيفة 20–30 دقيقة يوميًا",
                      "النوم من 7–8 ساعات ليلًا", "تقليل الأكل المتأخر قبل النوم"]
        risk, label = "منخفض", "بدون مرض مزمن محدد"

    if bmi_status == "نقص في الوزن":
        habits.append("إضافة وجبة خفيفة صحية بين الوجبات لزيادة السعرات بشكل تدريجي")
    elif bmi_status == "زيادة في الوزن":
        habits.append("التركيز على تقليل المقليات والحلويات مع زيادة الخضروات")
    elif bmi_status == "سمنة":
        habits.append("استشارة أخصائي تغذية لوضع خطة نزول وزن آمنة ومنضبطة")

    return recommended, forbidden, habits, risk, label


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NutriGuard AI — مساعدك الغذائي الذكي",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');

* { font-family: 'Tajawal', sans-serif !important; }

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* ── Hero Header ── */
.hero-title {
    text-align: center;
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(90deg, #a8edea, #fed6e3, #a8edea);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 3s linear infinite;
    margin-bottom: 0.2rem;
}
.hero-subtitle {
    text-align: center;
    color: #c4b5fd;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

/* ── Glass card ── */
.glass-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    backdrop-filter: blur(12px);
    margin-bottom: 1.5rem;
}

/* ── Result boxes ── */
.metric-box {
    background: rgba(168,237,234,0.12);
    border: 1px solid rgba(168,237,234,0.4);
    border-radius: 14px;
    padding: 1rem 1.5rem;
    text-align: center;
    margin-bottom: 0.8rem;
}
.metric-value { font-size: 2rem; font-weight: 900; color: #a8edea; }
.metric-label { color: #ddd; font-size: 0.9rem; }

/* ── Section headings ── */
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #fed6e3;
    border-right: 4px solid #a8edea;
    padding-right: 10px;
    margin: 1.2rem 0 0.6rem;
    direction: rtl;
}

/* ── List items ── */
.food-item {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    margin-bottom: 5px;
    color: #e2e8f0;
    font-size: 0.97rem;
    direction: rtl;
}
.food-item.green  { border-right: 3px solid #4ade80; }
.food-item.red    { border-right: 3px solid #f87171; }
.food-item.yellow { border-right: 3px solid #fbbf24; }

/* ── Risk badge ── */
.risk-badge {
    display: inline-block;
    padding: 4px 18px;
    border-radius: 50px;
    font-weight: 700;
    font-size: 1rem;
}
.risk-low    { background: rgba(74,222,128,0.25); color: #4ade80; border: 1px solid #4ade80; }
.risk-medium { background: rgba(251,191,36,0.25); color: #fbbf24; border: 1px solid #fbbf24; }
.risk-high   { background: rgba(248,113,113,0.25); color: #f87171; border: 1px solid #f87171; }

/* ── AI badge ── */
.ai-badge {
    display: inline-block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 12px;
    border-radius: 50px;
    margin-bottom: 0.5rem;
}

/* ── Message box ── */
.msg-box {
    background: rgba(102,126,234,0.15);
    border: 1px solid rgba(102,126,234,0.45);
    border-radius: 14px;
    padding: 1rem 1.5rem;
    color: #e2e8f0;
    font-size: 1rem;
    line-height: 1.7;
    direction: rtl;
    text-align: right;
}

/* ── Streamlit widgets ── */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label {
    color: #c4b5fd !important;
    font-weight: 600;
    direction: rtl;
}
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
    border-radius: 10px !important;
}

/* ── Button ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.8rem !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    font-family: 'Tajawal', sans-serif !important;
    cursor: pointer;
    transition: opacity 0.2s;
    margin-top: 0.5rem;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── RTL direction ── */
.rtl { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="hero-title">🥗 NutriGuard AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">مساعدك الغذائي الذكي — أدخل بياناتك واحصل على خطة مخصصة فورًا</div>',
    unsafe_allow_html=True,
)

if not (_GEMINI_AVAILABLE and _GEMINI_API_KEY):
    st.warning(
        "⚠️ مفتاح Gemini API غير موجود — سيتم استخدام الخطة الاحتياطية المدمجة. "
        "لتفعيل الذكاء الاصطناعي أضف `GEMINI_API_KEY` في Secrets بـ Streamlit Cloud.",
        icon="🔑",
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  INPUT FORM
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### 📋 بياناتك الشخصية", unsafe_allow_html=False)

col1, col2 = st.columns(2)
with col1:
    weight = st.number_input(
        "⚖️ الوزن (كيلوجرام)",
        min_value=20.0, max_value=300.0, value=70.0, step=0.5,
        key="weight_input",
    )
    age = st.number_input(
        "🎂 العمر (سنة)",
        min_value=1, max_value=120, value=30, step=1,
        key="age_input",
    )
with col2:
    height = st.number_input(
        "📏 الطول (سنتيمتر)",
        min_value=50.0, max_value=250.0, value=170.0, step=0.5,
        key="height_input",
    )

DISEASE_OPTIONS = {
    "لا يوجد مرض مزمن":             "none",
    "السكري (Diabetes)":             "diabetes",
    "ارتفاع ضغط الدم (Hypertension)": "hypertension",
    "ارتفاع الكوليسترول (Cholesterol)": "cholesterol",
    "أخرى / other":                  "other",
}

disease_label = st.selectbox(
    "🏥 الحالة الصحية / المرض المزمن",
    options=list(DISEASE_OPTIONS.keys()),
    key="disease_select",
)
chronic_disease = DISEASE_OPTIONS[disease_label]

# Custom disease entry if "أخرى"
if chronic_disease == "other":
    chronic_disease = st.text_input(
        "✏️ اكتب اسم المرض بالإنجليزية أو العربية",
        value="other",
        key="custom_disease",
    ).strip() or "other"

st.markdown('</div>', unsafe_allow_html=True)

# ── Analyse button ────────────────────────────────────────────────────────────
analyze_clicked = st.button("🔍 تحليل وعرض الخطة الغذائية", key="analyze_btn")

# ═══════════════════════════════════════════════════════════════════════════════
#  RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

if analyze_clicked:
    with st.spinner("⏳ جارٍ تحليل بياناتك وإعداد الخطة الغذائية..."):

        # Core calculations
        bmi            = _calculate_bmi(weight, height)
        bmi_status     = _classify_bmi(bmi)
        daily_calories = _estimate_daily_calories(weight, age)

        # AI or fallback
        ai_plan = _gemini_plan(bmi, bmi_status, daily_calories, chronic_disease)

        if ai_plan:
            recommended = list(ai_plan.get("recommended_foods", []))
            forbidden   = list(ai_plan.get("forbidden_foods", []))
            habits      = list(ai_plan.get("health_habits", []))
            risk        = str(ai_plan.get("risk_level", "متوسط"))
            message     = str(ai_plan.get("message", ""))
            used_ai     = True
        else:
            recommended, forbidden, habits, risk, disease_label = _fallback_plan(
                chronic_disease, bmi_status
            )
            message = (
                f"بناءً على مؤشر كتلة الجسم لديك البالغ {bmi} ({bmi_status}) "
                f"وحالتك الصحية: {disease_label}، نوصي بالتركيز على الأطعمة "
                "الموصى بها وتقليل الأطعمة غير المناسبة للحفاظ على توازن غذائي "
                f"أفضل. احتياجك التقريبي اليومي من السعرات حوالي {daily_calories} سعرة."
            )
            used_ai = False

    # ── Key Metrics ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📊 نتائج التحليل", unsafe_allow_html=False)

    if used_ai:
        st.markdown('<span class="ai-badge">✨ مدعوم بالذكاء الاصطناعي Gemini</span>',
                    unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="metric-box"><div class="metric-value">{bmi}</div>'
            '<div class="metric-label">مؤشر كتلة الجسم BMI</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-box"><div class="metric-value">{bmi_status}</div>'
            '<div class="metric-label">تصنيف الوزن</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        risk_cls = {"منخفض": "risk-low", "متوسط": "risk-medium", "مرتفع": "risk-high"}.get(risk, "risk-medium")
        st.markdown(
            f'<div class="metric-box"><div class="metric-value">'
            f'<span class="risk-badge {risk_cls}">{risk}</span></div>'
            '<div class="metric-label">مستوى الخطر</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="metric-box"><div class="metric-value">{daily_calories:,} سعرة</div>'
        '<div class="metric-label">الاحتياج التقريبي اليومي من السعرات الحرارية</div></div>',
        unsafe_allow_html=True,
    )

    # ── Recommended Foods ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">✅ الأطعمة الموصى بها</div>', unsafe_allow_html=True)
    for item in recommended:
        st.markdown(f'<div class="food-item green">🥦 {item}</div>', unsafe_allow_html=True)

    # ── Forbidden Foods ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">❌ الأطعمة التي يُنصح بتجنبها</div>', unsafe_allow_html=True)
    for item in forbidden:
        st.markdown(f'<div class="food-item red">🚫 {item}</div>', unsafe_allow_html=True)

    # ── Health Habits ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title">💡 عادات وتوصيات صحية يومية</div>', unsafe_allow_html=True)
    for item in habits:
        st.markdown(f'<div class="food-item yellow">⭐ {item}</div>', unsafe_allow_html=True)

    # ── Motivational Message ───────────────────────────────────────────────
    if message:
        st.markdown('<div class="section-title">💬 رسالة شخصية لك</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msg-box">{message}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("⚕️ **تنبيه:** هذا التطبيق للأغراض التعليمية فقط. يُرجى استشارة طبيبك أو أخصائي التغذية قبل تغيير نظامك الغذائي.")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<br><div style='text-align:center;color:#6b7280;font-size:0.8rem;'>"
    "NutriGuard AI © 2025 — مبني بـ 🐍 Python و ❤️ Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
