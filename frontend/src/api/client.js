import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 60000,
});

export async function health() {
  const { data } = await api.get("/api/health");
  return data;
}

export async function analyzeScreenshot(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function modelInfo() {
  const { data } = await api.get("/api/model/info");
  return data;
}
