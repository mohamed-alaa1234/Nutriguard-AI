import { analyze } from "./api.js";

const analyzeForm = document.getElementById("analyze-form");
const analyzeSubmit = document.getElementById("analyze-submit");
const caloriesValueEl = document.getElementById("daily-calories-value");
const bmiValueEl = document.getElementById("bmi-value");
const summaryValueEl = document.getElementById("summary-value");
const recommendedFoodsList = document.getElementById(
  "recommended-foods-list"
);
const dailyHabitsList = document.getElementById("daily-habits-list");
const forbiddenFoodsList = document.getElementById("forbidden-foods-list");
const toastEl = document.getElementById("toast");
const toggleThemeBtn = document.getElementById("toggle-theme");

function setLoading(button, isLoading) {
  const label = button.querySelector(".btn-label");
  const spinner = button.querySelector(".btn-spinner");

  if (isLoading) {
    button.disabled = true;
    if (label) label.classList.add("opacity-0");
    if (spinner) spinner.classList.remove("hidden");
  } else {
    button.disabled = false;
    if (label) label.classList.remove("opacity-0");
    if (spinner) spinner.classList.add("hidden");
  }
}

function showToast(message, type = "success") {
  if (!toastEl) return;
  toastEl.textContent = message;
  const baseClasses =
    "backdrop-blur bg-slate-900/95 text-slate-100 border-slate-700";
  const typeClass =
    type === "error"
      ? "bg-red-600/90 border-red-500 text-white"
      : "bg-emerald-600/90 border-emerald-500 text-white";
  toastEl.className = `${baseClasses} ${typeClass} fixed left-1/2 -translate-x-1/2 bottom-6 z-50 min-w-[260px] max-w-sm px-4 py-3 rounded-2xl text-sm shadow-lg border`;
  toastEl.classList.remove("hidden", "opacity-0", "translate-y-4");
  toastEl.classList.add("opacity-100", "translate-y-0");

  setTimeout(() => {
    toastEl.classList.add("opacity-0", "translate-y-4");
    setTimeout(() => {
      toastEl.classList.add("hidden");
    }, 250);
  }, 3000);
}

if (analyzeForm && analyzeSubmit) {
  analyzeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(analyzeForm);
    const weight = Number(form.get("weight_kg"));
    const height = Number(form.get("height_cm"));
    const age = Number(form.get("age"));
    const chronicDisease = String(form.get("chronic_disease") || "").trim();

    if (!weight || !height || !age || !chronicDisease) {
      showToast("الرجاء إدخال كل القيم قبل التحليل.", "error");
      return;
    }

    try {
      setLoading(analyzeSubmit, true);
      const payload = {
        weight_kg: weight,
        height_cm: height,
        age,
        chronic_disease: chronicDisease,
      };
      const result = await analyze(payload);

      if (caloriesValueEl) {
        caloriesValueEl.textContent = `${result.daily_calories} kcal`;
      }
      if (bmiValueEl) {
        bmiValueEl.textContent = result.bmi.toFixed(1);
      }
      if (summaryValueEl) {
        summaryValueEl.textContent = result.message;
      }

      const recommended =
        typeof result.recommended_foods === "string"
          ? [result.recommended_foods]
          : Array.isArray(result.recommended_foods)
          ? result.recommended_foods
          : [];
      const habits =
        typeof result.health_habits === "string"
          ? [result.health_habits]
          : Array.isArray(result.health_habits)
          ? result.health_habits
          : [];
      const forbidden =
        typeof result.forbidden_foods === "string"
          ? [result.forbidden_foods]
          : Array.isArray(result.forbidden_foods)
          ? result.forbidden_foods
          : [];

      if (recommendedFoodsList) {
        recommendedFoodsList.innerHTML = "";
        recommended.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          recommendedFoodsList.appendChild(li);
        });
      }

      if (dailyHabitsList) {
        dailyHabitsList.innerHTML = "";
        habits.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          dailyHabitsList.appendChild(li);
        });
      }

      if (forbiddenFoodsList) {
        forbiddenFoodsList.innerHTML = "";
        forbidden.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = item;
          forbiddenFoodsList.appendChild(li);
        });
      }

      showToast("تم تحليل بياناتك الغذائية بنجاح.");
    } catch (error) {
      showToast(error.message || "تعذر إجراء التحليل.", "error");
    } finally {
      setLoading(analyzeSubmit, false);
    }
  });
}

toggleThemeBtn.addEventListener("click", () => {
  const root = document.documentElement;
  const isDark = root.classList.contains("dark");
  if (isDark) {
    root.classList.remove("dark");
    toggleThemeBtn.textContent = "☾";
  } else {
    root.classList.add("dark");
    toggleThemeBtn.textContent = "☀";
  }
});

