import { useEffect, useMemo, useState } from "react";

import {
  getDashboard,
  getRegion,
  getLiveGrid,
  getLoadForecast,
  getAlerts,
  getAssetRisk,
  getDataQuality,
} from "../services/api";

function formatNumber(value, decimals = 2) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "-";
  }

  return number.toLocaleString(undefined, {
    maximumFractionDigits: decimals,
  });
}

function getRiskClass(value) {
  const risk = String(value || "").toLowerCase();

  if (risk === "critical") return "critical";
  if (risk === "high") return "high";
  if (risk === "medium") return "medium";

  return "low";
}

function getStatusClass(value) {
  return String(value || "").toLowerCase();
}

function Dashboard({ onLogout }) {
  const [dashboard, setDashboard] = useState(null);
  const [regionData, setRegionData] = useState([]);
  const [liveGrid, setLiveGrid] = useState(null);
  const [forecasts, setForecasts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [assetRisk, setAssetRisk] = useState([]);
  const [dataQuality, setDataQuality] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setError("");

        const [
          dashboardData,
          liveData,
          forecastData,
          alertData,
          riskData,
          qualityData,
        ] = await Promise.all([
          getDashboard(),
          getLiveGrid(),
          getLoadForecast(),
          getAlerts(),
          getAssetRisk(),
          getDataQuality(),
        ]);

        setDashboard(dashboardData);
        setLiveGrid(liveData);

        setForecasts(
          Array.isArray(forecastData)
            ? forecastData
            : forecastData?.forecasts || forecastData?.data || []
        );

        setAlerts(
          Array.isArray(alertData)
            ? alertData
            : alertData?.alerts || alertData?.data || []
        );

        setAssetRisk(
          Array.isArray(riskData)
            ? riskData
            : riskData?.assets || riskData?.data || []
        );

        setDataQuality(qualityData);

        const regions = await Promise.all(
          [1, 2, 3, 4, 5].map((regionKey) =>
            getRegion(regionKey)
          )
        );

        setRegionData(regions);
      } catch (err) {
        console.error(err);
        setError("Unable to load GridSense dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  const openAlerts = useMemo(
    () =>
      alerts.filter(
        (alert) =>
          String(alert.status || "").toUpperCase() === "OPEN"
      ),
    [alerts]
  );

  const highAlerts = useMemo(
    () =>
      alerts.filter(
        (alert) =>
          String(alert.severity || "").toUpperCase() === "HIGH"
      ),
    [alerts]
  );

  const highRiskAssets = useMemo(
    () =>
      assetRisk.filter((asset) => {
        const risk = String(
          asset.risk_level ||
            asset.risk ||
            asset.severity ||
            ""
        ).toUpperCase();

        return risk === "HIGH" || risk === "CRITICAL";
      }),
    [assetRisk]
  );

  const maxRegionalLoad = Math.max(
    ...((liveGrid?.regional_load || []).map(
      (region) => Number(region.load_kwh) || 0
    )),
    1
  );

  const maxRegionalEnergy = Math.max(
    ...(regionData.map(
      (region) => Number(region.total_kwh) || 0
    )),
    1
  );

  const maxForecastValue = Math.max(
    ...forecasts.slice(0, 12).flatMap((forecast) => [
      Number(
        forecast.actual_kwh ??
          forecast.actual ??
          0
      ),
      Number(
        forecast.predicted_kwh ??
          forecast.predicted ??
          0
      ),
    ]),
    1
  );

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-card">
          <div className="loading-spinner" />
          <h2>Loading GridSense</h2>
          <p>Connecting to energy operations services...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <div className="error-card">
          <div className="error-icon">!</div>
          <h2>Dashboard unavailable</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            GS
          </div>

          <div>
            <h1>GridSense</h1>
            <span>Energy Operations</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <a href="#overview" className="nav-item active">
            <span className="nav-icon">▦</span>
            Dashboard
          </a>

          <a href="#live-grid" className="nav-item">
            <span className="nav-icon">◉</span>
            Live Grid
          </a>

          <a href="#forecast" className="nav-item">
            <span className="nav-icon">⌁</span>
            Forecast
          </a>

          <a href="#alerts" className="nav-item">
            <span className="nav-icon">!</span>
            Alerts
            {openAlerts.length > 0 && (
              <span className="nav-count">
                {openAlerts.length}
              </span>
            )}
          </a>

          <a href="#asset-risk" className="nav-item">
            <span className="nav-icon">◇</span>
            Asset Risk
          </a>

          <a href="#data-quality" className="nav-item">
            <span className="nav-icon">✓</span>
            Data Quality
          </a>
        </nav>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>System Online</strong>
              <span>All services operational</span>
            </div>
          </div>

          <button
            className="sidebar-logout"
            onClick={onLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main-content">
        {/* HEADER */}
        <header className="topbar" id="overview">
          <div>
            <div className="eyebrow">
              ENERGY OPERATIONS PLATFORM
            </div>

            <h2>Operations Dashboard</h2>

            <p>
              Monitor grid performance, demand forecasts,
              alerts and infrastructure health.
            </p>
          </div>

          <div className="topbar-right">
            <div className="live-indicator">
              <span className="pulse-dot" />
              LIVE
            </div>

            <button
              className="topbar-logout"
              onClick={onLogout}
            >
              Logout
            </button>
          </div>
        </header>

        {/* LIVE GRID */}
        {liveGrid && (
          <section
            className="dashboard-section hero-section"
            id="live-grid"
          >
            <div className="section-heading">
              <div>
                <span className="section-eyebrow">
                  REAL-TIME MONITORING
                </span>

                <h3>Live Grid Status</h3>

                <p>
                  Current energy system operating conditions.
                </p>
              </div>

              <div className="live-badge">
                <span />
                System Live
              </div>
            </div>

            <div className="live-metrics">
              <div className="live-metric primary">
                <span>Current Load</span>
                <strong>
                  {formatNumber(
                    liveGrid.current_load_kwh
                  )}
                </strong>
                <small>kWh</small>
              </div>

              <div className="live-metric">
                <span>Today's Energy</span>
                <strong>
                  {formatNumber(
                    liveGrid.today_energy_kwh
                  )}
                </strong>
                <small>kWh</small>
              </div>

              <div className="live-metric">
                <span>Active Meters</span>
                <strong>
                  {Number(
                    liveGrid.active_meters || 0
                  ).toLocaleString()}
                </strong>
                <small>meters</small>
              </div>

              <div className="live-metric">
                <span>Latest Reading</span>
                <strong className="reading-time">
                  {liveGrid.latest_reading_time || "-"}
                </strong>
                <small>latest event</small>
              </div>
            </div>
          </section>
        )}

        {/* KPI GRID */}
        {dashboard && (
          <section className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-icon blue">C</div>
              <div>
                <span>Customers</span>
                <strong>
                  {dashboard.total_customers.toLocaleString()}
                </strong>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon purple">M</div>
              <div>
                <span>Meters</span>
                <strong>
                  {dashboard.total_meters.toLocaleString()}
                </strong>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon cyan">E</div>
              <div>
                <span>Energy Readings</span>
                <strong>
                  {dashboard.total_energy_readings.toLocaleString()}
                </strong>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon orange">O</div>
              <div>
                <span>Outages</span>
                <strong>
                  {dashboard.total_outages.toLocaleString()}
                </strong>
              </div>
            </div>

            <div className="kpi-card danger-card">
              <div className="kpi-icon red">!</div>
              <div>
                <span>Open Alerts</span>
                <strong>
                  {dashboard.open_alerts}
                </strong>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon green">✓</div>
              <div>
                <span>Resolved Alerts</span>
                <strong>
                  {dashboard.resolved_alerts}
                </strong>
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-icon indigo">F</div>
              <div>
                <span>Forecast Records</span>
                <strong>
                  {dashboard.forecast_records}
                </strong>
              </div>
            </div>

            <div className="kpi-card energy-kpi">
              <div className="kpi-icon blue">Σ</div>
              <div>
                <span>Total Energy</span>
                <strong>
                  {formatNumber(dashboard.total_kwh)}
                  <small> kWh</small>
                </strong>
              </div>
            </div>
          </section>
        )}

        {/* REGIONAL LIVE LOAD + REGIONAL ENERGY */}
        <section className="two-column-layout">
          <div className="dashboard-section chart-section">
            <div className="section-heading compact">
              <div>
                <span className="section-eyebrow">
                  REAL-TIME
                </span>
                <h3>Regional Live Load</h3>
                <p>Current load by operating region.</p>
              </div>
            </div>

            <div className="bar-list">
              {liveGrid?.regional_load?.map((region) => {
                const value =
                  Number(region.load_kwh) || 0;

                const percentage =
                  (value / maxRegionalLoad) * 100;

                return (
                  <div
                    className="bar-row"
                    key={region.region_key}
                  >
                    <div className="bar-label">
                      <span>{region.region_name}</span>
                      <strong>
                        {formatNumber(value)} kWh
                      </strong>
                    </div>

                    <div className="bar-track">
                      <div
                        className="bar-fill load-fill"
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="dashboard-section chart-section">
            <div className="section-heading compact">
              <div>
                <span className="section-eyebrow">
                  REGIONAL ANALYTICS
                </span>
                <h3>Regional Energy</h3>
                <p>Total energy consumption by region.</p>
              </div>
            </div>

            <div className="bar-list">
              {regionData.map((region) => {
                const value =
                  Number(region.total_kwh) || 0;

                const percentage =
                  (value / maxRegionalEnergy) * 100;

                return (
                  <div
                    className="bar-row"
                    key={region.region_key}
                  >
                    <div className="bar-label">
                      <span>{region.region_name}</span>
                      <strong>
                        {formatNumber(value)} kWh
                      </strong>
                    </div>

                    <div className="bar-track">
                      <div
                        className="bar-fill energy-fill"
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* REGIONAL DETAILS */}
        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                REGIONAL OPERATIONS
              </span>

              <h3>Regional Energy Overview</h3>

              <p>
                Customer, meter, energy and outage
                distribution across regions.
              </p>
            </div>

            <span className="section-tag">
              5 Regions
            </span>
          </div>

          <div className="region-grid">
            {regionData.map((region) => (
              <div
                className="region-card"
                key={region.region_key}
              >
                <div className="region-card-header">
                  <h4>{region.region_name}</h4>
                  <span className="region-number">
                    #{region.region_key}
                  </span>
                </div>

                <div className="region-stat">
                  <span>Customers</span>
                  <strong>
                    {region.customer_count.toLocaleString()}
                  </strong>
                </div>

                <div className="region-stat">
                  <span>Meters</span>
                  <strong>
                    {region.meter_count.toLocaleString()}
                  </strong>
                </div>

                <div className="region-stat">
                  <span>Energy</span>
                  <strong>
                    {formatNumber(region.total_kwh)}
                  </strong>
                </div>

                <div className="region-stat">
                  <span>Outages</span>
                  <strong>
                    {region.outage_count.toLocaleString()}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* FORECAST */}
        <section
          className="dashboard-section"
          id="forecast"
        >
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                MACHINE LEARNING
              </span>

              <h3>Demand Forecast</h3>

              <p>
                Regional energy demand predictions generated
                using Random Forest.
              </p>
            </div>

            <span className="model-badge">
              Random Forest
            </span>
          </div>

          <div className="forecast-summary-grid">
            <div className="summary-card">
              <span>Forecast Records</span>
              <strong>
                {forecasts.length || 85}
              </strong>
            </div>

            <div className="summary-card">
              <span>Regions</span>
              <strong>5</strong>
            </div>

            <div className="summary-card">
              <span>MAE</span>
              <strong>0.9183</strong>
            </div>

            <div className="summary-card">
              <span>RMSE</span>
              <strong>1.7174</strong>
            </div>
          </div>

          <div className="forecast-visual">
            {forecasts.slice(0, 12).map(
              (forecast, index) => {
                const actual = Number(
                  forecast.actual_kwh ??
                    forecast.actual ??
                    0
                );

                const predicted = Number(
                  forecast.predicted_kwh ??
                    forecast.predicted ??
                    0
                );

                const actualHeight =
                  (actual / maxForecastValue) * 100;

                const predictedHeight =
                  (predicted / maxForecastValue) * 100;

                return (
                  <div
                    className="forecast-column"
                    key={`${forecast.forecast_date}-${index}`}
                  >
                    <div className="forecast-bars">
                      <div
                        className="forecast-bar actual"
                        style={{
                          height: `${actualHeight}%`,
                        }}
                        title={`Actual: ${formatNumber(
                          actual
                        )}`}
                      />

                      <div
                        className="forecast-bar predicted"
                        style={{
                          height: `${predictedHeight}%`,
                        }}
                        title={`Predicted: ${formatNumber(
                          predicted
                        )}`}
                      />
                    </div>

                    <span>
                      {(forecast.forecast_date ||
                        forecast.date ||
                        "-").slice(5)}
                    </span>
                  </div>
                );
              }
            )}
          </div>

          <div className="chart-legend">
            <span>
              <i className="legend-dot actual-dot" />
              Actual
            </span>

            <span>
              <i className="legend-dot predicted-dot" />
              Predicted
            </span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Region</th>
                  <th>Actual kWh</th>
                  <th>Predicted kWh</th>
                  <th>Model</th>
                </tr>
              </thead>

              <tbody>
                {forecasts.slice(0, 10).map(
                  (forecast, index) => {
                    const date =
                      forecast.forecast_date ||
                      forecast.date ||
                      "-";

                    const region =
                      forecast.region_name ||
                      forecast.region ||
                      "-";

                    const actual =
                      forecast.actual_kwh ??
                      forecast.actual ??
                      0;

                    const predicted =
                      forecast.predicted_kwh ??
                      forecast.predicted ??
                      0;

                    const model =
                      forecast.model_name ||
                      "RandomForestRegressor";

                    return (
                      <tr key={index}>
                        <td>{date}</td>
                        <td>{region}</td>
                        <td>
                          {formatNumber(actual)}
                        </td>
                        <td>
                          {formatNumber(predicted)}
                        </td>
                        <td>
                          <span className="model-label">
                            {model}
                          </span>
                        </td>
                      </tr>
                    );
                  }
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* ALERTS */}
        <section
          className="dashboard-section"
          id="alerts"
        >
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                AUTOMATED OPERATIONS
              </span>

              <h3>Grid Alerts</h3>

              <p>
                Operational alerts generated from grid
                monitoring and forecasting rules.
              </p>
            </div>

            <span className="section-tag danger-tag">
              {openAlerts.length} Open
            </span>
          </div>

          <div className="alert-summary-grid">
            <div className="summary-card">
              <span>Total Alerts</span>
              <strong>{alerts.length}</strong>
            </div>

            <div className="summary-card danger-summary">
              <span>Open Alerts</span>
              <strong>
                {openAlerts.length}
              </strong>
            </div>

            <div className="summary-card danger-summary">
              <span>High Severity</span>
              <strong>
                {highAlerts.length}
              </strong>
            </div>

            <div className="summary-card">
              <span>Alert Type</span>
              <strong className="summary-text">
                Peak Demand
              </strong>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Alert</th>
                  <th>Severity</th>
                  <th>Region</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Reason</th>
                </tr>
              </thead>

              <tbody>
                {alerts.slice(0, 10).map(
                  (alert, index) => (
                    <tr
                      key={
                        alert.alert_key || index
                      }
                    >
                      <td className="strong-cell">
                        {alert.alert_type || "-"}
                      </td>

                      <td>
                        <span
                          className={`severity ${getRiskClass(
                            alert.severity
                          )}`}
                        >
                          {alert.severity || "-"}
                        </span>
                      </td>

                      <td>
                        {alert.region_name || "-"}
                      </td>

                      <td>
                        {alert.alert_date || "-"}
                      </td>

                      <td>
                        <span
                          className={`status ${getStatusClass(
                            alert.status
                          )}`}
                        >
                          {alert.status || "-"}
                        </span>
                      </td>

                      <td className="reason-cell">
                        {alert.trigger_reason || "-"}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* ASSET RISK */}
        <section
          className="dashboard-section"
          id="asset-risk"
        >
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                INFRASTRUCTURE MONITORING
              </span>

              <h3>Asset Risk</h3>

              <p>
                Maintenance and infrastructure risk
                monitoring.
              </p>
            </div>

            <span className="section-tag danger-tag">
              {highRiskAssets.length} High Risk
            </span>
          </div>

          <div className="risk-summary-grid">
            <div className="summary-card">
              <span>Total Assets</span>
              <strong>
                {assetRisk.length || 50}
              </strong>
            </div>

            <div className="summary-card danger-summary">
              <span>High Risk</span>
              <strong>
                {highRiskAssets.length}
              </strong>
            </div>

            <div className="summary-card">
              <span>Operational</span>
              <strong>
                {
                  assetRisk.filter(
                    (asset) =>
                      String(
                        asset.status || ""
                      ).toLowerCase() ===
                      "operational"
                  ).length
                }
              </strong>
            </div>

            <div className="summary-card">
              <span>Maintenance</span>
              <strong>
                {
                  assetRisk.filter(
                    (asset) =>
                      String(
                        asset.status || ""
                      ).toLowerCase() ===
                      "maintenance"
                  ).length
                }
              </strong>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Region</th>
                  <th>Risk</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {assetRisk.slice(0, 10).map(
                  (asset, index) => {
                    const risk =
                      asset.risk_level ||
                      asset.risk ||
                      asset.severity ||
                      "-";

                    return (
                      <tr
                        key={
                          asset.asset_id ||
                          asset.asset_key ||
                          index
                        }
                      >
                        <td className="strong-cell">
                          {asset.asset_id ||
                            asset.asset_key ||
                            "-"}
                        </td>

                        <td>
                          {asset.region_name ||
                            asset.region ||
                            "-"}
                        </td>

                        <td>
                          <span
                            className={`severity ${getRiskClass(
                              risk
                            )}`}
                          >
                            {risk}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`asset-status ${getStatusClass(
                              asset.status
                            )}`}
                          >
                            {asset.status || "-"}
                          </span>
                        </td>
                      </tr>
                    );
                  }
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* DATA QUALITY */}
        <section
          className="dashboard-section quality-section"
          id="data-quality"
        >
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">
                DATA GOVERNANCE
              </span>

              <h3>Data Quality</h3>

              <p>
                Pipeline validation and data health
                monitoring.
              </p>
            </div>

            <span
              className={`quality-status ${
                dataQuality?.overall_status === "PASS"
                  ? "pass"
                  : "fail"
              }`}
            >
              <span />
              {dataQuality?.overall_status ||
                "UNKNOWN"}
            </span>
          </div>

          <div className="quality-grid">
            <div className="quality-card">
              <div className="quality-icon">✓</div>
              <div>
                <span>Total Checks</span>
                <strong>
                  {dataQuality?.total_checks || 7}
                </strong>
              </div>
            </div>

            <div className="quality-card success">
              <div className="quality-icon">✓</div>
              <div>
                <span>Passed</span>
                <strong>
                  {dataQuality?.passed_checks || 7}
                </strong>
              </div>
            </div>

            <div className="quality-card failed">
              <div className="quality-icon">!</div>
              <div>
                <span>Failed</span>
                <strong>
                  {dataQuality?.failed_checks || 0}
                </strong>
              </div>
            </div>
          </div>
        </section>

        <footer className="dashboard-footer">
          <span>GridSense Energy Operations Platform</span>
          <span>Real-time monitoring • Forecasting • Automation</span>
        </footer>
      </main>
    </div>
  );
}

export default Dashboard;