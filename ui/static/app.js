/**
 * JobHunter Germany - Frontend Application Logic (v1.1)
 * Multi-keyword search support & customizable Excel save location.
 */

let allJobs = [];
let currentFilteredJobs = [];
let isPyWebView = false;
let currentExcelPath = "";
let currentExcelDownloadUrl = "";

// DOM Elements
const searchForm = document.getElementById("searchForm");
const inputKeyword = document.getElementById("inputKeyword");
const inputLocation = document.getElementById("inputLocation");
const inputSaveDir = document.getElementById("inputSaveDir");
const btnBrowseSaveDir = document.getElementById("btnBrowseSaveDir");

const selectDistance = document.getElementById("selectDistance");
const selectJobType = document.getElementById("selectJobType");
const selectDate = document.getElementById("selectDate");
const selectLimit = document.getElementById("selectLimit");
const chkRemote = document.getElementById("chkRemote");
const btnSearch = document.getElementById("btnSearch");
const searchIcon = document.getElementById("searchIcon");
const searchText = document.getElementById("searchText");

const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");
const progressMessage = document.getElementById("progressMessage");

const statTotal = document.getElementById("statTotal");
const statATS = document.getElementById("statATS");
const statRemote = document.getElementById("statRemote");
const statPlatforms = document.getElementById("statPlatforms");

const filterInput = document.getElementById("filterInput");
const filterTabs = document.querySelectorAll(".filter-tab");

const welcomeState = document.getElementById("welcomeState");
const loadingState = document.getElementById("loadingState");
const loadingStatusText = document.getElementById("loadingStatusText");
const resultsTableContainer = document.getElementById("resultsTableContainer");
const resultsTableBody = document.getElementById("resultsTableBody");

const excelReadyBanner = document.getElementById("excelReadyBanner");
const excelFileFolder = document.getElementById("excelFileFolder");
const excelFileName = document.getElementById("excelFileName");
const btnOpenExcelDirect = document.getElementById("btnOpenExcelDirect");
const btnExportExcel = document.getElementById("btnExportExcel");
const btnOpenFolder = document.getElementById("btnOpenFolder");
const footerInfo = document.getElementById("footerInfo");

const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toastMessage");
const toastIcon = document.getElementById("toastIcon");

// Initialize PyWebView listener
window.addEventListener("pywebviewready", async () => {
  isPyWebView = true;
  document.getElementById("connectionStatus").innerHTML = `
    <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
    <span>Desktop App Mode</span>
  `;
  initSaveDirectory();
});

// Initialize Save Directory
async function initSaveDirectory() {
  const saved = localStorage.getItem("jobhunter_save_dir");
  if (saved) {
    inputSaveDir.value = saved;
  } else {
    try {
      if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.get_default_save_dir) {
        const defaultDir = await window.pywebview.api.get_default_save_dir();
        inputSaveDir.value = defaultDir;
      } else {
        const resp = await fetch("/api/get_save_dir");
        const data = await resp.json();
        inputSaveDir.value = data.path || "./exports";
      }
    } catch (e) {
      inputSaveDir.value = "./exports";
    }
  }
}

// Ensure init happens on regular browser mode as well
document.addEventListener("DOMContentLoaded", () => {
  initSaveDirectory();
});

// Toast notification helper
function showToast(message, icon = "ℹ️", duration = 5000) {
  toastMessage.textContent = message;
  toastIcon.textContent = icon;
  toast.classList.remove("translate-y-20", "opacity-0");
  toast.classList.add("translate-y-0", "opacity-100");

  setTimeout(() => {
    toast.classList.remove("translate-y-0", "opacity-100");
    toast.classList.add("translate-y-20", "opacity-0");
  }, duration);
}

// Preset Chips clicks (supports appending multiple keywords)
document.querySelectorAll(".preset-chip").forEach(btn => {
  btn.addEventListener("click", () => {
    const kw = btn.getAttribute("data-kw");
    const current = inputKeyword.value.trim();
    if (!current) {
      inputKeyword.value = kw;
    } else {
      const parts = current.split(",").map(p => p.trim());
      if (!parts.includes(kw)) {
        inputKeyword.value = `${current}, ${kw}`;
      }
    }
    inputKeyword.focus();
  });
});

// City Chips clicks
document.querySelectorAll(".city-chip").forEach(btn => {
  btn.addEventListener("click", () => {
    inputLocation.value = btn.getAttribute("data-loc");
  });
});

// Browse Save Directory Button
if (btnBrowseSaveDir) {
  btnBrowseSaveDir.addEventListener("click", async () => {
    try {
      let chosen = "";
      if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.select_save_directory) {
        chosen = await window.pywebview.api.select_save_directory();
      } else {
        const resp = await fetch("/api/select_folder", { method: "POST" });
        const data = await resp.json();
        chosen = data.path;
      }

      if (chosen) {
        inputSaveDir.value = chosen;
        localStorage.setItem("jobhunter_save_dir", chosen);
        showToast("Save location set to: " + chosen, "📁");
      }
    } catch (e) {
      const promptVal = prompt("Enter full folder path to save Excel files:", inputSaveDir.value);
      if (promptVal) {
        inputSaveDir.value = promptVal.trim();
        localStorage.setItem("jobhunter_save_dir", promptVal.trim());
      }
    }
  });
}

// Quick start button in welcome state
const btnQuickStart = document.getElementById("btnQuickStart");
if (btnQuickStart) {
  btnQuickStart.addEventListener("click", () => {
    inputKeyword.value = "Python Developer, Data Engineer";
    inputLocation.value = "Berlin";
    searchForm.dispatchEvent(new Event("submit"));
  });
}

// Open link in browser helper
function openUrl(url) {
  if (!url) return;
  if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.open_in_browser) {
    window.pywebview.api.open_in_browser(url);
  } else {
    window.open(url, "_blank");
  }
}

// Open Excel File Helper
async function launchExcelFile(targetPath) {
  try {
    if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.open_excel_file) {
      await window.pywebview.api.open_excel_file(targetPath || currentExcelPath);
    } else {
      const resp = await fetch("/api/open_file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: targetPath || currentExcelPath })
      });
      const data = await resp.json();
      if (!data.success && currentExcelDownloadUrl) {
        window.open(currentExcelDownloadUrl, "_blank");
      }
    }
    showToast("Launching Excel spreadsheet...", "📊");
  } catch (e) {
    if (currentExcelDownloadUrl) {
      window.open(currentExcelDownloadUrl, "_blank");
    } else {
      showToast("Could not open file automatically: " + e.message, "⚠️");
    }
  }
}

if (btnOpenExcelDirect) {
  btnOpenExcelDirect.addEventListener("click", () => {
    launchExcelFile(currentExcelPath);
  });
}

// Open exports folder
if (btnOpenFolder) {
  btnOpenFolder.addEventListener("click", async () => {
    const saveDir = inputSaveDir.value.trim();
    try {
      if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.open_exports_folder) {
        await window.pywebview.api.open_exports_folder(saveDir);
      } else {
        const resp = await fetch("/api/open_folder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: saveDir })
        });
        const res = await resp.json();
        showToast("Opened: " + (res.path || saveDir), "📁");
      }
    } catch (e) {
      showToast("Files saved in: " + saveDir, "📁");
    }
  });
}

// Collect form filters
function getFormFilters() {
  const sources = [];
  document.querySelectorAll("input[name='sources']:checked").forEach(cb => {
    sources.push(cb.value);
  });

  return {
    keyword: inputKeyword.value.trim(),
    location: inputLocation.value.trim() || "Deutschland",
    distance: parseInt(selectDistance.value) || 50,
    job_type: selectJobType.value || null,
    date_posted_days: selectDate.value ? parseInt(selectDate.value) : null,
    results_per_source: parseInt(selectLimit.value) || 25,
    is_remote: chkRemote.checked,
    save_directory: inputSaveDir.value.trim() || null,
    sources: sources.length > 0 ? sources : ["arbeitsagentur", "indeed", "linkedin"]
  };
}

// Execute search
searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const filters = getFormFilters();

  if (!filters.keyword) {
    showToast("Please enter at least one job title or keyword.", "⚠️");
    return;
  }

  // Count keywords
  const kwList = filters.keyword.split(/[,;\n]+/).map(k => k.trim()).filter(Boolean);
  const kwCount = kwList.length;

  // Set Loading UI
  welcomeState.classList.add("hidden");
  resultsTableContainer.classList.add("hidden");
  excelReadyBanner.classList.add("hidden");
  loadingState.classList.remove("hidden");
  loadingStatusText.textContent = `Searching for ${kwCount} keyword(s) across Germany and compiling Excel...`;

  progressContainer.classList.remove("hidden");
  progressBar.style.width = "20%";
  progressMessage.innerHTML = `<span>Querying German platforms for: ${escapeHtml(kwList.join(', '))}...</span>`;

  btnSearch.disabled = true;
  btnSearch.classList.add("opacity-60", "cursor-not-allowed");
  searchIcon.textContent = "⏳";
  searchText.textContent = "Searching & Building Excel...";

  try {
    let resultData = null;

    if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.search_jobs) {
      progressBar.style.width = "60%";
      resultData = await window.pywebview.api.search_jobs(filters);
    } else {
      progressBar.style.width = "50%";
      const resp = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters)
      });
      resultData = await resp.json();
    }

    progressBar.style.width = "100%";

    if (resultData && resultData.jobs) {
      allJobs = resultData.jobs;
      currentFilteredJobs = [...allJobs];
      renderStats(resultData.stats || calculateStats(allJobs));
      renderResults(currentFilteredJobs);

      // Handle Auto-Generated Excel Sheet
      if (resultData.excel_path && resultData.excel_filename) {
        currentExcelPath = resultData.excel_path;
        currentExcelDownloadUrl = resultData.download_url || "";
        excelFileName.textContent = resultData.excel_filename;
        excelFileFolder.textContent = resultData.save_directory || inputSaveDir.value;
        excelReadyBanner.classList.remove("hidden");
        showToast(`Found ${allJobs.length} jobs! Saved to: ${resultData.excel_filename}`, "📊", 6000);
      } else {
        showToast(`Found ${allJobs.length} jobs in Germany!`, "🎉");
      }

      footerInfo.textContent = `Displaying ${allJobs.length} unique listings across ${kwCount} keyword(s). Excel file generated.`;
    } else {
      throw new Error(resultData?.error || "No response received.");
    }

  } catch (err) {
    console.error("Search error:", err);
    showToast("Search failed: " + err.message, "❌");
    footerInfo.textContent = "Search error occurred. Please try again.";
  } finally {
    loadingState.classList.add("hidden");
    btnSearch.disabled = false;
    btnSearch.classList.remove("opacity-60", "cursor-not-allowed");
    searchIcon.textContent = "🔍";
    searchText.textContent = "Find Jobs & Generate Excel";
    setTimeout(() => {
      progressContainer.classList.add("hidden");
      progressBar.style.width = "0%";
    }, 1200);
  }
});

// Calculate statistics client-side if needed
function calculateStats(jobs) {
  const total = jobs.length;
  const atsCount = jobs.filter(j => j.application_type === "Direct ATS").length;
  const remoteCount = jobs.filter(j => j.is_remote).length;
  const platforms = new Set();
  jobs.forEach(j => {
    (j.found_on || [j.source_platform]).forEach(p => platforms.add(p));
  });

  return {
    total_jobs: total,
    direct_ats_jobs: atsCount,
    remote_jobs: remoteCount,
    active_sources_count: platforms.size
  };
}

// Render statistics
function renderStats(stats) {
  statTotal.textContent = stats.total_jobs || 0;
  statATS.textContent = stats.direct_ats_jobs || 0;
  statRemote.textContent = stats.remote_jobs || 0;
  statPlatforms.textContent = stats.active_sources_count || Object.keys(stats.platform_distribution || {}).length || 0;
}

// Generate platform badge HTML
function getPlatformBadge(platform, appType) {
  const pLower = (platform || "").toLowerCase();
  
  if (pLower.includes("workday")) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-workday">Workday ATS</span>`;
  } else if (pLower.includes("personio")) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-personio">Personio ATS</span>`;
  } else if (pLower.includes("greenhouse")) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-greenhouse">Greenhouse</span>`;
  } else if (pLower.includes("lever")) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-lever">Lever</span>`;
  } else if (pLower.includes("arbeitsagentur") || pLower.includes("bundesagentur")) {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-arbeitsagentur">Bundesagentur für Arbeit</span>`;
  } else if (appType === "Direct ATS") {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${platform} ATS</span>`;
  } else {
    return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold badge-jobboard">${platform || "Job Board"}</span>`;
  }
}

// Render Results Table
function renderResults(jobs) {
  if (!jobs || jobs.length === 0) {
    resultsTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="py-12 text-center text-slate-400">
          <p class="text-sm font-medium">No matching jobs found with the current filters.</p>
          <p class="text-xs text-slate-500 mt-1">Try broadening your keywords or increasing search radius.</p>
        </td>
      </tr>
    `;
    resultsTableContainer.classList.remove("hidden");
    return;
  }

  resultsTableBody.innerHTML = jobs.map((job) => {
    const isDirectAts = job.application_type === "Direct ATS";
    const applyUrl = job.direct_apply_url || job.job_url;
    const foundPlatforms = (job.found_on && job.found_on.length > 0) ? job.found_on.join(", ") : job.source_platform;
    const matchedKws = (job.matched_keywords && job.matched_keywords.length > 0) ? job.matched_keywords : [];

    return `
      <tr class="hover:bg-slate-800/40 transition group ${isDirectAts ? 'bg-blue-950/10' : ''}">
        
        <!-- Title & Company -->
        <td class="py-3.5 px-4 max-w-xs sm:max-w-sm">
          <div class="font-semibold text-slate-100 group-hover:text-blue-400 transition text-sm flex items-center space-x-1.5">
            ${isDirectAts ? '<span title="Direct ATS Application" class="text-blue-400 text-xs">⚡</span>' : ''}
            <span>${escapeHtml(job.title)}</span>
          </div>
          <div class="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
            <span class="font-medium text-slate-300">${escapeHtml(job.company)}</span>
            <span>•</span>
            <span class="text-slate-500" title="Found on: ${escapeHtml(foundPlatforms)}">Found: ${escapeHtml(foundPlatforms)}</span>
          </div>

          <!-- Matched Keywords badges -->
          ${matchedKws.length > 0 ? `
            <div class="flex flex-wrap gap-1 mt-1">
              ${matchedKws.map(k => `<span class="px-1.5 py-0.2 rounded text-[10px] bg-blue-900/40 text-blue-300 border border-blue-700/50">🔑 ${escapeHtml(k)}</span>`).join('')}
            </div>
          ` : ''}

          ${job.description_snippet ? `
            <p class="text-[11px] text-slate-500 line-clamp-1 mt-1">${escapeHtml(job.description_snippet)}</p>
          ` : ''}
        </td>

        <!-- Location & Type -->
        <td class="py-3.5 px-3 whitespace-nowrap">
          <div class="text-slate-200 font-medium">${escapeHtml(job.location || 'Deutschland')}</div>
          <div class="flex items-center space-x-1.5 mt-0.5">
            ${job.is_remote ? `
              <span class="px-1.5 py-0.2 text-[10px] rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Remote</span>
            ` : ''}
            <span class="text-[11px] text-slate-500">${escapeHtml(job.job_type || 'Full-time')}</span>
          </div>
        </td>

        <!-- Application Platform -->
        <td class="py-3.5 px-3 whitespace-nowrap">
          <div>${getPlatformBadge(job.application_platform, job.application_type)}</div>
          <div class="text-[10px] text-slate-500 mt-1">${escapeHtml(job.application_type)}</div>
        </td>

        <!-- How to Apply -->
        <td class="py-3.5 px-4 text-xs text-slate-300 max-w-xs">
          <p class="line-clamp-2 leading-relaxed">${escapeHtml(job.how_to_apply || 'Click apply to visit application page.')}</p>
          ${job.salary && job.salary !== 'Not specified' ? `
            <div class="text-[10px] text-amber-400 font-medium mt-0.5">💰 ${escapeHtml(job.salary)}</div>
          ` : ''}
        </td>

        <!-- Actions -->
        <td class="py-3.5 px-3 text-right whitespace-nowrap">
          <div class="flex items-center justify-end space-x-2">
            <button 
              onclick="openUrl('${encodeURI(applyUrl)}')" 
              class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-sm transition flex items-center space-x-1 cursor-pointer"
            >
              <span>Apply</span>
              <span>↗</span>
            </button>
            ${job.job_url && job.job_url !== applyUrl ? `
              <button 
                onclick="openUrl('${encodeURI(job.job_url)}')" 
                title="View original aggregator listing"
                class="px-2 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                <span>Portal</span>
              </button>
            ` : ''}
          </div>
        </td>

      </tr>
    `;
  }).join("");

  resultsTableContainer.classList.remove("hidden");
}

// Instant in-page search / text filter
filterInput.addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();
  applyFilters(query, getActiveTabFilter());
});

// Tab filters (All, Workday, Personio, Remote, Bundesagentur)
filterTabs.forEach(tab => {
  tab.addEventListener("click", () => {
    filterTabs.forEach(t => {
      t.classList.remove("active", "bg-blue-600", "text-white");
      t.classList.add("bg-slate-800", "text-slate-300");
    });
    tab.classList.add("active", "bg-blue-600", "text-white");
    tab.classList.remove("bg-slate-800", "text-slate-300");

    applyFilters(filterInput.value.toLowerCase().trim(), tab.getAttribute("data-filter"));
  });
});

function getActiveTabFilter() {
  const activeTab = document.querySelector(".filter-tab.active");
  return activeTab ? activeTab.getAttribute("data-filter") : "all";
}

function applyFilters(query, tabFilter) {
  let filtered = [...allJobs];

  // 1. Tab Filter
  if (tabFilter === "workday") {
    filtered = filtered.filter(j => (j.application_platform || "").toLowerCase().includes("workday"));
  } else if (tabFilter === "personio") {
    filtered = filtered.filter(j => (j.application_platform || "").toLowerCase().includes("personio"));
  } else if (tabFilter === "remote") {
    filtered = filtered.filter(j => j.is_remote);
  } else if (tabFilter === "ba") {
    filtered = filtered.filter(j => (j.found_on || []).some(p => p.toLowerCase().includes("bundesagentur")));
  }

  // 2. Query Search
  if (query) {
    filtered = filtered.filter(j => {
      const matchTitle = (j.title || "").toLowerCase().includes(query);
      const matchComp = (j.company || "").toLowerCase().includes(query);
      const matchLoc = (j.location || "").toLowerCase().includes(query);
      const matchPlatform = (j.application_platform || "").toLowerCase().includes(query);
      const matchKws = (j.matched_keywords || []).some(k => k.toLowerCase().includes(query));
      return matchTitle || matchComp || matchLoc || matchPlatform || matchKws;
    });
  }

  currentFilteredJobs = filtered;
  renderResults(currentFilteredJobs);
  footerInfo.textContent = `Displaying ${filtered.length} of ${allJobs.length} jobs.`;
}

// Manual Export to Excel Handler
btnExportExcel.addEventListener("click", async () => {
  if (!allJobs || allJobs.length === 0) {
    showToast("Please search for jobs first before exporting.", "⚠️");
    return;
  }

  btnExportExcel.disabled = true;
  btnExportExcel.textContent = "Generating...";

  try {
    const saveDir = inputSaveDir.value.trim();
    let filePath = "";
    if (isPyWebView && window.pywebview && window.pywebview.api && window.pywebview.api.export_excel_manual) {
      filePath = await window.pywebview.api.export_excel_manual(saveDir);
    } else {
      const resp = await fetch("/api/export_excel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ save_directory: saveDir })
      });
      const data = await resp.json();
      filePath = data.path || "";
      if (data.download_url) {
        window.open(data.download_url, "_blank");
      }
    }

    currentExcelPath = filePath;
    showToast(`Excel spreadsheet saved to: ${filePath}`, "📊", 6000);
  } catch (err) {
    console.error("Export error:", err);
    showToast("Export failed: " + err.message, "❌");
  } finally {
    btnExportExcel.disabled = false;
    btnExportExcel.innerHTML = "<span>📊</span><span>Export to Excel</span>";
  }
});

// Utility to escape HTML
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
