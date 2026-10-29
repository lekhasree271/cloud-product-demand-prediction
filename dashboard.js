/**
 * Cloud-Based Product Demand Prediction System Dashboard
 * Chart.js Forecasting Visualizer, What-If Simulator, and Supply Chain Inventory Engine.
 */

(() => {
  // DOM Elements
  const productSelect = document.getElementById('productSelect');
  const modelSelect = document.getElementById('modelSelect');
  const horizonBtns = document.querySelectorAll('.horizon-toggle .toggle-btn');
  const discountSlider = document.getElementById('discountSlider');
  const discountVal = document.getElementById('discountVal');
  const promoToggle = document.getElementById('promoToggle');
  const holidayToggle = document.getElementById('holidayToggle');
  const btnRunForecast = document.getElementById('btnRunForecast');

  // KPI Elements
  const kpiProducts = document.getElementById('kpiProducts');
  const kpiCategories = document.getElementById('kpiCategories');
  const kpiRecords = document.getElementById('kpiRecords');
  const kpiR2 = document.getElementById('kpiR2');
  const kpiMae = document.getElementById('kpiMae');
  const kpiAlerts = document.getElementById('kpiAlerts');
  const activeModelLabel = document.getElementById('activeModelLabel');

  // Chart Elements
  const chartCanvas = document.getElementById('demandChart');
  const chartProductTitle = document.getElementById('chartProductTitle');
  const chartProductCategory = document.getElementById('chartProductCategory');
  let demandChart = null;

  // Inventory Elements
  const invCurrent = document.getElementById('invCurrent');
  const invPredicted = document.getElementById('invPredicted');
  const invSafetyStock = document.getElementById('invSafetyStock');
  const invROP = document.getElementById('invROP');
  const invEOQ = document.getElementById('invEOQ');
  const invRunway = document.getElementById('invRunway');
  const alertBoxDynamic = document.getElementById('alertBoxDynamic');
  const alertIcon = document.getElementById('alertIcon');
  const alertHeading = document.getElementById('alertHeading');
  const alertBody = document.getElementById('alertBody');

  // Lists & Feeds
  const featureList = document.getElementById('featureList');
  const alertFeed = document.getElementById('alertFeed');
  const btnRefreshAlerts = document.getElementById('btnRefreshAlerts');

  // Modals
  const archModal = document.getElementById('archModal');
  const btnArchModal = document.getElementById('btnArchModal');
  const btnCloseArchModal = document.getElementById('btnCloseArchModal');
  const uploadModal = document.getElementById('uploadModal');
  const btnUploadModal = document.getElementById('btnUploadModal');
  const btnCloseUploadModal = document.getElementById('btnCloseUploadModal');
  const dropzone = document.getElementById('dropzone');
  const csvFileInput = document.getElementById('csvFileInput');
  const selectedFileName = document.getElementById('selectedFileName');
  const btnSubmitUpload = document.getElementById('btnSubmitUpload');
  const toast = document.getElementById('toastNotification');

  // State
  let currentHorizonDays = 14;
  let activeProducts = [];
  let selectedFile = null;

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // Horizon Selection
  horizonBtns.forEach((btn) => {
    btn.onclick = () => {
      horizonBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentHorizonDays = parseInt(btn.dataset.days);
      runForecast();
    };
  });

  // What-If Discount Slider
  discountSlider.oninput = (e) => {
    discountVal.textContent = `${e.target.value}%`;
  };

  // Algorithm Switcher
  modelSelect.onchange = async () => {
    const model_type = modelSelect.value;
    showToast(`Retraining ML engine with ${model_type}...`);
    try {
      const res = await fetch('/api/model/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_type })
      });
      if (res.ok) {
        const data = await res.json();
        activeModelLabel.textContent = data.model_type;
        kpiR2.textContent = data.metrics.r2_score;
        kpiMae.textContent = `MAE: ±${data.metrics.mae} Units`;
        renderFeatureImportances(data.top_features);
        showToast(`Model updated: ${model_type} (R²: ${data.metrics.r2_score})`);
        runForecast();
      }
    } catch (e) {
      showToast('Model training failed.');
    }
  };

  // Initialize Chart.js
  function initChart() {
    const ctx = chartCanvas.getContext('2d');
    demandChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Historical Actual Sales',
            data: [],
            borderColor: '#637b98',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 2,
            tension: 0.25
          },
          {
            label: 'Machine Learning Demand Forecast',
            data: [],
            borderColor: '#00d2b4',
            backgroundColor: 'rgba(0, 210, 180, 0.12)',
            fill: true,
            borderWidth: 3,
            pointRadius: 4,
            pointBackgroundColor: '#00d2b4',
            pointBorderColor: '#fff',
            pointHoverRadius: 6,
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#121e31',
            titleColor: '#fff',
            bodyColor: '#00d2b4',
            borderColor: '#1b2b44',
            borderWidth: 1,
            padding: 10
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(27, 43, 68, 0.4)' },
            ticks: { color: '#8295ab', maxTicksLimit: 12, font: { family: "'JetBrains Mono'" } }
          },
          y: {
            grid: { color: 'rgba(27, 43, 68, 0.4)' },
            ticks: { color: '#8295ab', font: { family: "'JetBrains Mono'" } },
            title: { display: true, text: 'Units Demanded', color: '#8295ab', font: { size: 11 } }
          }
        }
      }
    });
  }

  // Load Dataset Summary
  async function loadDatasetSummary() {
    try {
      const res = await fetch('/api/dataset/summary');
      if (!res.ok) return;
      const data = await res.json();

      kpiProducts.textContent = `${data.product_count} Products`;
      kpiCategories.textContent = `${Object.keys(data.categories).length} Categories`;
      kpiRecords.textContent = `${data.total_records.toLocaleString()} Records`;

      if (data.model_metrics) {
        kpiR2.textContent = data.model_metrics.r2_score || '0.89';
        kpiMae.textContent = `MAE: ±${data.model_metrics.mae || '2.4'} Units`;
        activeModelLabel.textContent = data.active_model || 'Random Forest';
      }

      activeProducts = data.products || [];
      productSelect.innerHTML = activeProducts.map((p) =>
        `<option value="${p.product_id}">${p.product_name} (${p.category}) - Stock: ${p.current_inventory} units</option>`
      ).join('');

      if (activeProducts.length > 0) {
        runForecast();
      }
    } catch (e) {
      console.error('Failed to load dataset summary:', e);
    }
  }

  // Run Forecast API
  async function runForecast() {
    const product_id = productSelect.value;
    if (!product_id) return;

    btnRunForecast.disabled = true;
    btnRunForecast.textContent = '⏳ Calculating Forecast...';

    const payload = {
      product_id: product_id,
      horizon_days: currentHorizonDays,
      discount_percent: parseFloat(discountSlider.value),
      promotional_campaign: promoToggle.checked ? 1 : 0,
      is_holiday: holidayToggle.checked ? 1 : 0
    };

    try {
      const res = await fetch('/api/predict/demand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        showToast(`Error: ${err.detail}`);
        return;
      }

      const data = await res.json();
      updateDashboardWithForecast(data);
    } catch (e) {
      showToast('Demand prediction calculation failed.');
    } finally {
      btnRunForecast.disabled = false;
      btnRunForecast.textContent = '⚡ Run Demand Forecast';
    }
  }

  // Update UI with Forecast Results
  function updateDashboardWithForecast(data) {
    chartProductTitle.textContent = `${data.product_name} · ${data.horizon_days}-Day Forecast`;
    chartProductCategory.textContent = `Category: ${data.category} · Unit Base Price: $${data.unit_price} · Simulated Discount: ${data.applied_discount_percent}%`;

    // Chart Data Preparation
    const historyDates = data.historical_recent_series.map((x) => x.date);
    const historyVals = data.historical_recent_series.map((x) => x.units_sold);

    const forecastDates = data.forecast_series.map((x) => x.date);
    const forecastVals = data.forecast_series.map((x) => x.predicted_units);

    // Merge dates
    const allLabels = [...historyDates, ...forecastDates];

    // Align historical line (null during forecast period)
    const historyAligned = [...historyVals, ...Array(forecastDates.length).fill(null)];

    // Connect forecast line (last history point connects to first forecast point)
    const lastHistoryVal = historyVals[historyVals.length - 1];
    const forecastAligned = [
      ...Array(historyDates.length - 1).fill(null),
      lastHistoryVal,
      ...forecastVals
    ];

    demandChart.data.labels = allLabels;
    demandChart.data.datasets[0].data = historyAligned;
    demandChart.data.datasets[1].data = forecastAligned;
    demandChart.update();

    // Inventory Panel
    const inv = data.inventory_analysis;
    invCurrent.textContent = `${inv.current_inventory} Units`;
    invPredicted.textContent = `${Math.round(data.total_predicted_units)} Units`;
    invSafetyStock.textContent = `${inv.safety_stock} Units`;
    invROP.textContent = `${inv.reorder_point} Units`;
    invEOQ.textContent = `${inv.recommended_order_quantity_eoq} Units`;
    invRunway.textContent = `${inv.days_of_supply} Days`;

    // Stockout vs Overstock Alert Banner
    const stockout = inv.stockout_risk;
    const overstock = inv.overstock_risk;

    if (stockout.urgency === 'URGENT' || stockout.urgency === 'HIGH') {
      alertBoxDynamic.className = 'alert-box-dynamic urgent';
      alertIcon.textContent = '🚨';
      alertHeading.textContent = `Reorder Alert · Stockout Risk ${stockout.risk_percentage}%`;
      alertBody.textContent = stockout.message;
    } else if (overstock.excess_units > 0) {
      alertBoxDynamic.className = 'alert-box-dynamic warning';
      alertIcon.textContent = '⚠️';
      alertHeading.textContent = `Overstock Warning · ${overstock.excess_units} Excess Units ($${overstock.capital_tied_up_usd.toLocaleString()})`;
      alertBody.textContent = overstock.message;
    } else {
      alertBoxDynamic.className = 'alert-box-dynamic normal';
      alertIcon.textContent = '✓';
      alertHeading.textContent = `Healthy Supply Chain · ${inv.days_of_supply} Days Runway`;
      alertBody.textContent = stockout.message;
    }

    loadAlerts();
  }

  // Render Feature Importances
  function renderFeatureImportances(features) {
    if (!features || features.length === 0) return;
    const maxVal = Math.max(...features.map((f) => f.importance));

    featureList.innerHTML = features.map((f) => {
      const pct = Math.round((f.importance / maxVal) * 100);
      const cleanName = f.feature
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (l) => l.toUpperCase());
      return `
        <div class="feature-bar-item">
          <div class="feature-header">
            <span>${cleanName}</span>
            <span class="text-teal">${(f.importance * 100).toFixed(1)}%</span>
          </div>
          <div class="feature-track">
            <div class="feature-fill" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Load Inventory Alerts from DynamoDB store
  async function loadAlerts() {
    try {
      const res = await fetch('/api/inventory/alerts');
      if (!res.ok) return;
      const data = await res.json();

      kpiAlerts.textContent = `${data.total_alerts} Active`;

      if (data.alerts.length === 0) {
        alertFeed.innerHTML = '<div class="empty-state">No stockout or overstock risks detected across catalog.</div>';
        return;
      }

      alertFeed.innerHTML = data.alerts.map((a) => {
        const cls = a.urgency === 'URGENT' || a.urgency === 'HIGH' ? 'urgent' : 'warning';
        return `
          <div class="alert-item ${cls}">
            <h5>${a.product_name} · [${a.alert_type.replace(/_/g, ' ')}]</h5>
            <p>${a.message}</p>
          </div>
        `;
      }).join('');
    } catch (_) {}
  }

  btnRefreshAlerts.onclick = loadAlerts;
  btnRunForecast.onclick = runForecast;
  productSelect.onchange = runForecast;

  // Modals
  btnArchModal.onclick = () => archModal.classList.add('show');
  btnCloseArchModal.onclick = () => archModal.classList.remove('show');
  btnUploadModal.onclick = () => uploadModal.classList.add('show');
  btnCloseUploadModal.onclick = () => uploadModal.classList.remove('show');

  window.onclick = (e) => {
    if (e.target === archModal) archModal.classList.remove('show');
    if (e.target === uploadModal) uploadModal.classList.remove('show');
  };

  // Drag and Drop CSV Upload
  dropzone.onclick = () => csvFileInput.click();
  csvFileInput.onchange = (e) => {
    if (e.target.files.length > 0) {
      selectedFile = e.target.files[0];
      selectedFileName.textContent = `Selected: ${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`;
      btnSubmitUpload.disabled = false;
    }
  };

  dropzone.ondragover = (e) => { e.preventDefault(); dropzone.style.borderColor = '#00d2b4'; };
  dropzone.ondragleave = () => { dropzone.style.borderColor = '#284065'; };
  dropzone.ondrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      selectedFile = e.dataTransfer.files[0];
      selectedFileName.textContent = `Selected: ${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`;
      btnSubmitUpload.disabled = false;
    }
  };

  btnSubmitUpload.onclick = async () => {
    if (!selectedFile) return;
    btnSubmitUpload.disabled = true;
    btnSubmitUpload.textContent = '⏳ Uploading to S3 & Training...';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/dataset/upload', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        showToast(`Upload failed: ${err.detail}`);
        return;
      }

      const result = await res.json();
      showToast(`Dataset uploaded to ${result.s3_metadata.storage_provider}! Retrained on ${result.records} rows.`);
      uploadModal.classList.remove('show');
      loadDatasetSummary();
    } catch (e) {
      showToast('Error uploading dataset.');
    } finally {
      btnSubmitUpload.disabled = false;
      btnSubmitUpload.textContent = 'Upload & Retrain ML Model';
    }
  };

  // Boot
  initChart();
  loadDatasetSummary();
  loadAlerts();
})();
