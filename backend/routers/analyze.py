import json
import os
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
from fastapi import APIRouter

from .. import schemas

router = APIRouter()


def _configure_gemini() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)


_configure_gemini()
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m**2), 1)


def _classify_bmi(bmi: float) -> str:
    if bmi <= 0:
        return "غير معروف"
    if bmi < 18.5:
        return "نقص في الوزن"
    if bmi < 25:
        return "وزن طبيعي"
    if bmi < 30:
        return "زيادة في الوزن"
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


def _gemini_plan(
    bmi: float,
    bmi_status: str,
    daily_calories: int,
    chronic_disease: str,
) -> Dict[str, Any] | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
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
        model = genai.GenerativeModel(_GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = response.text or ""
        return _parse_ai_json(text)
    except Exception:
        return None


def _fallback_plan(
    chronic_disease: str,
    bmi_status: str,
) -> Tuple[List[str], List[str], List[str], str, str]:
    disease = chronic_disease.lower()

    if "diab" in disease:
        recommended = [
            "خضروات ورقية داكنة",
            "حبوب كاملة مثل الشوفان",
            "عدس وبقوليات",
            "بروتينات خفيفة مثل الدجاج المشوي",
            "مكسرات غير مملحة",
        ]
        forbidden = [
            "مشروبات غازية محلاة",
            "حلويات بكثرة السكر",
            "خبز أبيض وأرز أبيض",
        ]
        habits = [
            "المشي 30 دقيقة يوميًا بعد الوجبات",
            "توزيع الكربوهيدرات على وجبات صغيرة",
            "قياس سكر الدم بانتظام بالتنسيق مع الطبيب",
        ]
        risk = "متوسط"
        label = "السكري"
    elif "hyper" in disease or "ضغط" in disease:
        recommended = [
            "خضروات طازجة متنوعة",
            "أطعمة قليلة الملح",
            "زيت الزيتون كبديل للدهون الصلبة",
            "فواكه غنية بالبوتاسيوم مثل الموز",
            "أسماك مشوية",
        ]
        forbidden = [
            "أطعمة معلبة عالية الصوديوم",
            "وجبات سريعة",
            "مخللات كثيرة الملح",
        ]
        habits = [
            "قياس ضغط الدم بانتظام",
            "تقليل إضافة الملح على المائدة",
            "ممارسة نشاط بدني معتدل 5 أيام في الأسبوع",
        ]
        risk = "متوسط"
        label = "ارتفاع ضغط الدم"
    elif "chol" in disease or "دهون" in disease:
        recommended = [
            "أسماك دهنية صحية مثل السلمون",
            "مكسرات غير مملحة",
            "حبوب كاملة مثل الشوفان والشعير",
            "أطعمة غنية بالألياف مثل التفاح",
            "زيت الزيتون والأفوكادو",
        ]
        forbidden = [
            "أطعمة مقلية",
            "دهون مشبعة مثل السمن الصناعي",
            "لحوم مصنّعة",
        ]
        habits = [
            "استبدال القلي بالشوي أو السلق",
            "الحد من صفار البيض واللحوم الدسمة",
            "إدخال تمارين هوائية خفيفة بانتظام",
        ]
        risk = "مرتفع"
        label = "ارتفاع الكوليسترول"
    else:
        recommended = [
            "خضروات موسمية متنوعة",
            "فواكه طازجة بكميات معتدلة",
            "ماء كافٍ على مدار اليوم",
            "بروتين متوازن من مصادر مختلفة",
            "حبوب كاملة بدلًا من المكررة",
        ]
        forbidden = [
            "مشروبات محلاة بشكل متكرر",
            "مقالي متكررة",
            "وجبات سريعة غنية بالدهون",
        ]
        habits = [
            "المشي أو الحركة الخفيفة 20–30 دقيقة يوميًا",
            "النوم من 7–8 ساعات ليلًا",
            "تقليل الأكل المتأخر قبل النوم",
        ]
        risk = "منخفض"
        label = "بدون مرض مزمن محدد"

    if bmi_status == "نقص في الوزن":
        habits.append(
            "إضافة وجبة خفيفة صحية بين الوجبات لزيادة السعرات بشكل تدريجي"
        )
    elif bmi_status == "زيادة في الوزن":
        habits.append(
            "التركيز على تقليل المقليات والحلويات مع زيادة الخضروات"
        )
    elif bmi_status == "سمنة":
        habits.append(
            "استشارة أخصائي تغذية لوضع خطة نزول وزن آمنة ومنضبطة"
        )

    return recommended, forbidden, habits, risk, label


@router.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(data: schemas.AnalyzeRequest) -> schemas.AnalyzeResponse:
    bmi = _calculate_bmi(weight_kg=data.weight_kg, height_cm=data.height_cm)
    bmi_status = _classify_bmi(bmi)
    daily_calories = _estimate_daily_calories(
        weight_kg=data.weight_kg,
        age=data.age,
    )

    ai_plan = _gemini_plan(
        bmi=bmi,
        bmi_status=bmi_status,
        daily_calories=daily_calories,
        chronic_disease=data.chronic_disease,
    )

    if ai_plan:
        recommended = list(ai_plan.get("recommended_foods", []))
        forbidden = list(ai_plan.get("forbidden_foods", []))
        habits = list(ai_plan.get("health_habits", []))
        risk = str(ai_plan.get("risk_level", "متوسط"))
        message = str(ai_plan.get("message", ""))
        disease_label = data.chronic_disease
    else:
        recommended, forbidden, habits, risk, disease_label = _fallback_plan(
            data.chronic_disease,
            bmi_status,
        )
        message = (
            f"بناءً على مؤشر كتلة الجسم لديك البالغ {bmi} ({bmi_status}) "
            f"وحالتك الصحية: {disease_label}، نوصي بالتركيز على الأطعمة "
            "الموصى بها وتقليل الأطعمة غير المناسبة للحفاظ على توازن غذائي "
            f"أفضل. احتياجك التقريبي اليومي من السعرات حوالي {daily_calories} "
            "سعرة."
        )

    return schemas.AnalyzeResponse(
        bmi=bmi,
        bmi_status=bmi_status,
        daily_calories=daily_calories,
        recommended_foods=recommended,
        forbidden_foods=forbidden,
        health_habits=habits,
        risk_level=risk,
        message=message,
    )

