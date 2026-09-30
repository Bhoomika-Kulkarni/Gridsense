import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

/* =========================================================
   Authentication
   ========================================================= */

export const login = async (username, password) => {
  const formData = new URLSearchParams();

  formData.append("username", username);
  formData.append("password", password);

  const response = await api.post(
    "/api/auth/login",
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  localStorage.setItem(
    "access_token",
    response.data.access_token
  );

  return response.data;
};

/* =========================================================
   Helper
   ========================================================= */

const authHeaders = () => {
  const token = localStorage.getItem("access_token");

  return {
    Authorization: `Bearer ${token}`,
  };
};

/* =========================================================
   Dashboard
   ========================================================= */

export const getDashboard = async () => {
  const response = await api.get(
    "/api/dashboard",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Regions
   ========================================================= */

export const getRegion = async (regionKey) => {
  const response = await api.get(
    `/api/regions/${regionKey}`,
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Live Grid
   ========================================================= */

export const getLiveGrid = async () => {
  const response = await api.get(
    "/api/grid/live",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Load Forecast
   ========================================================= */

export const getLoadForecast = async () => {
  const response = await api.get(
    "/api/load-forecast",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Alerts
   ========================================================= */

export const getAlerts = async () => {
  const response = await api.get(
    "/api/alerts",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Asset Risk
   ========================================================= */

export const getAssetRisk = async () => {
  const response = await api.get(
    "/api/assets/risk",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Data Quality
   ========================================================= */

export const getDataQuality = async () => {
  const response = await api.get(
    "/api/data-quality",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

/* =========================================================
   Other APIs
   ========================================================= */

export const getOutages = async () => {
  const response = await api.get(
    "/api/outages",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

export const getEventsLive = async () => {
  const response = await api.get(
    "/api/events/live",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

export const getForecasts = async () => {
  const response = await api.get(
    "/api/forecasts",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

export const getRisk = async () => {
  const response = await api.get(
    "/api/risk",
    {
      headers: authHeaders(),
    }
  );

  return response.data;
};

export default api;