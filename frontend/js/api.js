const API_BASE_URL = "http://127.0.0.1:8000";

function buildHeaders() {
  return {
    "Content-Type": "application/json",
  };
}

async function handleResponse(response) {
  const contentType = response.headers.get("Content-Type") || "";
  let data;
  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message =
      (data && data.detail) ||
      (typeof data === "string" ? data : "حدث خطأ غير متوقع.");
    throw new Error(message);
  }

  return data;
}

export async function analyze(payload) {
  const url = `${API_BASE_URL}/api/v1/analyze`;
  console.log("Sending data to:", url);
  console.log("Data:", payload);
  const response = await fetch(url, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

