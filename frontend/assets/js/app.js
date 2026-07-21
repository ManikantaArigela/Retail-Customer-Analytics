// Application Router, Search, Filters and UI State Controller

document.addEventListener("DOMContentLoaded", () => {
    App.init();
});

const App = {
    currentUser: null,
    currentView: null,
    
    // Global filter state object (mapping all 18+ dimensions)
    globalFilters: {
        start_date: "",
        end_date: "",
        business_category: "",
        store: "",
        region: "",
        country: "",
        state: "",
        city: "",
        product_category: "",
        brand: "",
        supplier: "",
        customer_type: "",
        sales_channel: "",
        payment_method: "",
        inventory_status: "",
        year: "",
        quarter: "",
        month: "",
        week: "",
        product: "",
        gender: "",
        day: ""
    },

    init() {
        this.setupEventListeners();
        this.checkAuth();
    },

    setupEventListeners() {
        // Handle session expiry event
        window.addEventListener("auth-expired", () => {
            this.showToast("Your session has expired. Please log in again.", "error");
            this.navigate("login");
        });

        // Navigation links (Sidebar & Data-target elements)
        document.querySelectorAll("[data-target]").forEach(element => {
            element.addEventListener("click", (e) => {
                e.preventDefault();
                const target = element.getAttribute("data-target");
                if (target) {
                    this.navigate(target);
                }
            });
        });

        // Sidebar Collapse Button
        const collapseBtn = document.getElementById("collapse-sidebar-btn");
        if (collapseBtn) {
            collapseBtn.addEventListener("click", () => {
                const sidebar = document.getElementById("sidebar");
                if (sidebar) {
                    sidebar.classList.toggle("collapsed");
                }
            });
        }

        // Top-bar Category Selector Sync
        const topbarCategorySelect = document.getElementById("topbar-category-select");
        if (topbarCategorySelect) {
            topbarCategorySelect.addEventListener("change", () => {
                const val = topbarCategorySelect.value;
                this.globalFilters.business_category = val;
                
                // Update drawer/inline select
                const inlineSelect = document.getElementById("filter-business-category");
                if (inlineSelect) inlineSelect.value = val;
                
                this.showToast(`Retail sector filter applied: ${val ? val.toUpperCase() : "All Sectors"}`, "info");
                this.refreshCurrentView();
            });
        }

        // Refresh Dashboard Button
        const refreshBtn = document.getElementById("refresh-dashboard-btn");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", () => {
                this.showToast("Refreshing metrics & data ledger...", "info");
                this.refreshCurrentView();
            });
        }

        // Topbar Search Input
        const searchInput = document.getElementById("topbar-search-input");
        if (searchInput) {
            searchInput.addEventListener("input", (e) => {
                const query = e.target.value.toLowerCase().trim();
                const txSearchInput = document.getElementById("tx-search-input");
                if (txSearchInput) {
                    txSearchInput.value = query;
                    txSearchInput.dispatchEvent(new Event("input"));
                }
            });
        }

        // Bind real-time change events on all 22 filters
        const filterIds = [
            "start-date", "end-date", "business-category", "store", "region",
            "country", "state", "city", "product-category", "brand",
            "supplier", "customer-type", "sales-channel", "payment-method", "inventory-status",
            "year", "quarter", "month", "week", "product", "gender", "day"
        ];
        
        filterIds.forEach(id => {
            const el = document.getElementById(`filter-${id}`);
            if (el) {
                el.addEventListener("change", () => {
                    this.readFiltersFromUI();
                    
                    // Sync topbar category select if category changed
                    if (id === "business-category" && topbarCategorySelect) {
                        topbarCategorySelect.value = el.value || "";
                    }
                    
                    this.refreshCurrentView();
                });
                
                if (el.type === "date") {
                    el.addEventListener("input", () => {
                        this.readFiltersFromUI();
                        this.refreshCurrentView();
                    });
                }
            }
        });

        // Apply Filters Button
        const applyFiltersBtn = document.getElementById("apply-filters-btn");
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener("click", () => {
                this.readFiltersFromUI();
                this.showToast("Filter parameters applied across all metrics.", "success");
                this.refreshCurrentView();
            });
        }

        // Reset Filters Button
        const resetFiltersBtn = document.getElementById("reset-filters-btn");
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener("click", () => {
                this.resetFiltersUI();
                this.readFiltersFromUI();
                if (topbarCategorySelect) topbarCategorySelect.value = "";
                this.showToast("All filters reset to defaults.", "info");
                this.refreshCurrentView();
            });
        }

        // Clear All Filters Button
        const clearFiltersBtn = document.getElementById("clear-filters-btn");
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener("click", () => {
                this.resetFiltersUI();
                this.readFiltersFromUI();
                
                if (topbarCategorySelect) {
                    topbarCategorySelect.value = "";
                }
                
                this.showToast("All dimension filters cleared.", "info");
                this.refreshCurrentView();
            });
        }

        // Notifications trigger action
        const notifyBtn = document.getElementById("trigger-notifications");
        if (notifyBtn) {
            notifyBtn.addEventListener("click", () => {
                this.showToast("No critical stockout or churn anomalies detected. BI Engine healthy.", "success");
                const badge = notifyBtn.querySelector(".badge");
                if (badge) badge.style.display = "none";
            });
        }

        // Logout button
        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                API.removeToken();
                this.currentUser = null;
                this.showToast("Logged out successfully.", "success");
                this.navigate("login");
            });
        }
        
        // Fullscreen Modal close
        const closeFullscreenBtn = document.getElementById("close-fullscreen-modal-btn");
        const modal = document.getElementById("chart-fullscreen-modal");
        if (closeFullscreenBtn && modal) {
            closeFullscreenBtn.addEventListener("click", () => {
                modal.style.display = "none";
                if (typeof Charts !== "undefined") {
                    Charts.destroy("fullscreen-chart-canvas");
                }
            });
        }

        // Login & Register Form Handlers
        const loginForm = document.getElementById("login-form");
        if (loginForm) {
            loginForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const usernameEl = document.getElementById("login-username");
                const passwordEl = document.getElementById("login-password");
                const username = usernameEl ? usernameEl.value.trim() : "";
                const password = passwordEl ? passwordEl.value : "";
                
                if (!username || !password) {
                    this.showToast("Please enter both username and password.", "error");
                    return;
                }
                
                try {
                    this.showLoader("Authenticating credentials...");
                    const res = await API.request("/auth/login", {
                        method: "POST",
                        body: JSON.stringify({ username, password })
                    });
                    
                    API.setToken(res.access_token);
                    this.showToast("Login successful! Welcome back.", "success");
                    await this.checkAuth();
                } catch (err) {
                    this.showToast(err.message || "Authentication failed. Incorrect username or password.", "error");
                } finally {
                    this.hideLoader();
                }
            });
        }

        const registerForm = document.getElementById("register-form");
        if (registerForm) {
            registerForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const username = document.getElementById("reg-username")?.value.trim();
                const email = document.getElementById("reg-email")?.value.trim();
                const password = document.getElementById("reg-password")?.value;
                const company = document.getElementById("reg-company")?.value.trim();
                const sector = document.getElementById("reg-sector")?.value;
                
                if (!username || !email || !password || !company) {
                    this.showToast("Please complete all registration fields.", "error");
                    return;
                }
                
                try {
                    this.showLoader("Registering new tenant profile...");
                    await API.request("/auth/register", {
                        method: "POST",
                        body: JSON.stringify({
                            username,
                            email,
                            password,
                            company_name: company,
                            business_category: sector
                        })
                    });
                    
                    this.showToast("Profile created! Authenticating...", "success");
                    
                    const loginRes = await API.request("/auth/login", {
                        method: "POST",
                        body: JSON.stringify({ username, password })
                    });
                    
                    API.setToken(loginRes.access_token);
                    await this.checkAuth();
                } catch (err) {
                    this.showToast(err.message || "Registration failed.", "error");
                } finally {
                    this.hideLoader();
                }
            });
        }

        // Toggle between login and register panels via links
        document.querySelectorAll("#show-register").forEach(el => {
            el.addEventListener("click", (e) => {
                e.preventDefault();
                const loginSection = document.getElementById("login-section");
                const registerSection = document.getElementById("register-section");
                if (loginSection && registerSection) {
                    loginSection.style.display = "none";
                    registerSection.style.display = "block";
                } else {
                    if (typeof App !== "undefined" && App.navigate) App.navigate("register");
                }
            });
        });

        document.querySelectorAll("#show-login").forEach(el => {
            el.addEventListener("click", (e) => {
                e.preventDefault();
                const loginSection = document.getElementById("login-section");
                const registerSection = document.getElementById("register-section");
                if (loginSection && registerSection) {
                    registerSection.style.display = "none";
                    loginSection.style.display = "block";
                } else {
                    if (typeof App !== "undefined" && App.navigate) App.navigate("login");
                }
            });
        });
    },

    readFiltersFromUI() {
        const filterIds = [
            "start-date", "end-date", "business-category", "store", "region",
            "country", "state", "city", "product-category", "brand",
            "supplier", "customer-type", "sales-channel", "payment-method", "inventory-status",
            "year", "quarter", "month", "week", "product", "gender", "day"
        ];
        
        filterIds.forEach(id => {
            const el = document.getElementById(`filter-${id}`);
            const key = id.replace(/-/g, "_");
            if (el) {
                this.globalFilters[key] = el.value || "";
            }
        });
    },

    resetFiltersUI() {
        const filterIds = [
            "start-date", "end-date", "business-category", "store", "region",
            "country", "state", "city", "product-category", "brand",
            "supplier", "customer-type", "sales-channel", "payment-method", "inventory-status",
            "year", "quarter", "month", "week", "product", "gender", "day"
        ];
        
        filterIds.forEach(id => {
            const el = document.getElementById(`filter-${id}`);
            if (el) {
                el.value = "";
            }
        });
        
        Object.keys(this.globalFilters).forEach(key => {
            this.globalFilters[key] = "";
        });
    },

    async checkAuth() {
        const token = API.getToken();
        if (!token) {
            this.navigate("login");
            return;
        }

        try {
            this.showLoader("Restoring session...");
            const user = await API.request("/auth/me");
            this.currentUser = user;
            this.updateUserProfileUI(user);
            this.hideLoader();

            try {
                const datasets = await API.request("/datasets");
                if (datasets && datasets.length > 0) {
                    this.navigate("dashboard");
                } else {
                    this.navigate("data-upload");
                    this.showToast("Welcome! Upload your dataset or download a sample to start.", "info");
                }
            } catch (dErr) {
                console.warn("Datasets check skipped:", dErr);
                this.navigate("dashboard");
            }
        } catch (error) {
            console.error("Auth check failed:", error);
            API.removeToken();
            this.hideLoader();
            this.navigate("login");
        }
    },

    updateUserProfileUI(user) {
        const sidebar = document.getElementById("sidebar");
        const topBar = document.getElementById("top-bar");
        if (sidebar) sidebar.style.display = "flex";
        if (topBar) topBar.style.display = "flex";

        const char = user.username ? user.username.charAt(0).toUpperCase() : "U";
        
        const avatar = document.getElementById("user-avatar-char");
        if (avatar) avatar.textContent = char;

        const topbarAvatar = document.getElementById("topbar-avatar-char");
        if (topbarAvatar) topbarAvatar.textContent = char;

        const nameNode = document.getElementById("user-name-text");
        if (nameNode) nameNode.textContent = user.username;

        const topName = document.getElementById("topbar-user-name");
        if (topName) topName.textContent = user.username;

        const companyNode = document.getElementById("user-company-text");
        if (companyNode) companyNode.textContent = user.company_name || "Enterprise Retailer";

        const topCompanyTag = document.getElementById("topbar-company-name");
        if (topCompanyTag) topCompanyTag.textContent = user.company_name || "AI Retail BI";

        const selectEl = document.getElementById("topbar-category-select");
        if (selectEl && user.business_category) {
            selectEl.value = user.business_category;
        }
    },

    async navigate(viewName) {
        if (this.currentView === viewName) return;

        // Destroy old Chart instances
        if (typeof Charts !== "undefined") {
            Object.keys(Charts.instances).forEach(id => Charts.destroy(id));
        }

        const viewId = `view-${viewName}`;
        const activeSection = document.getElementById(viewId);
        if (!activeSection) {
            console.error(`View section not found: ${viewName}`);
            return;
        }

        const sidebar = document.getElementById("sidebar");
        const topBar = document.getElementById("top-bar");

        if (viewName === "login") {
            if (sidebar) sidebar.style.display = "none";
            if (topBar) topBar.style.display = "none";
        } else {
            if (sidebar) sidebar.style.display = "flex";
            if (topBar) topBar.style.display = "flex";
        }

        // Hide all views
        document.querySelectorAll(".app-view").forEach(v => {
            v.style.display = "none";
        });

        // Show target view
        activeSection.style.display = "block";

        // Toggle global filters panel visibility
        const globalFiltersPanel = document.getElementById("global-filters-panel");
        if (globalFiltersPanel) {
            if (viewName === "login" || viewName === "data-upload") {
                globalFiltersPanel.style.display = "none";
            } else {
                globalFiltersPanel.style.display = "block";
            }
        }

        // Active state on sidebar items
        document.querySelectorAll(".menu-item").forEach(item => {
            item.classList.remove("active");
            if (item.getAttribute("data-target") === viewName) {
                item.classList.add("active");
            }
        });

        // Update Topbar Title
        const titleNode = document.getElementById("top-bar-title");
        if (titleNode) {
            const formatted = viewName.split("-").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
            titleNode.textContent = formatted;
        }

        this.currentView = viewName;
        this.showLoader(`Loading ${viewName}...`);

        try {
            this.initializeViewScript(viewName);
        } catch (error) {
            console.error("View initialization error:", error);
        } finally {
            this.hideLoader();
        }
    },

    initializeViewScript(viewName) {
        if (viewName === "dashboard" && typeof initDashboardView === "function") {
            initDashboardView(this);
        } else if (viewName === "analytics" && typeof initAnalyticsView === "function") {
            initAnalyticsView(this);
        } else if (viewName === "reports" && typeof initReportsView === "function") {
            initReportsView(this);
        } else if (viewName === "data-upload" && typeof initDataUploadView === "function") {
            initDataUploadView(this);
        } else if (viewName === "login" && typeof initLoginView === "function") {
            initLoginView(this);
        } else if (viewName === "ai-assistant" && typeof initAiAssistantView === "function") {
            initAiAssistantView(this);
        } else if (viewName === "settings" && typeof initSettingsView === "function") {
            initSettingsView(this);
        }
    },

    refreshCurrentView() {
        if (this.currentView === "dashboard" && typeof initDashboardView === "function") {
            initDashboardView(this);
        } else if (this.currentView === "analytics" && typeof initAnalyticsView === "function") {
            initAnalyticsView(this);
        }
    },

    showLoader(text = "Loading BI Engine...") {
        let loader = document.getElementById("global-loader");
        if (!loader) {
            const target = document.querySelector(".app-container") || document.body;
            loader = document.createElement("div");
            loader.id = "global-loader";
            loader.className = "loader-overlay";
            loader.innerHTML = `
                <div class="spinner"></div>
                <div class="loader-text" id="global-loader-text">${text}</div>
            `;
            target.appendChild(loader);
        } else {
            const textNode = document.getElementById("global-loader-text");
            if (textNode) textNode.textContent = text;
            loader.style.display = "flex";
        }
    },

    hideLoader() {
        const loader = document.getElementById("global-loader");
        if (loader) {
            loader.style.display = "none";
        }
    },

    showFullscreenChart(title, sourceCanvasId) {
        const modal = document.getElementById("chart-fullscreen-modal");
        const titleEl = document.getElementById("fullscreen-chart-title");
        const canvas = document.getElementById("fullscreen-chart-canvas");
        const sourceChart = Charts.instances[sourceCanvasId];
        
        if (!modal || !canvas || !sourceChart) return;
        
        titleEl.textContent = title;
        modal.style.display = "flex";
        
        const config = sourceChart.config;
        Charts.destroy("fullscreen-chart-canvas");
        
        const modalCtx = canvas.getContext("2d");
        Charts.instances["fullscreen-chart-canvas"] = new Chart(modalCtx, {
            type: config.type,
            data: JSON.parse(JSON.stringify(config.data)),
            options: {
                ...JSON.parse(JSON.stringify(config.options)),
                maintainAspectRatio: false,
                responsive: true
            }
        });
    },

    exportChartAsImage(canvasId, filename = "chart-export.png") {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        try {
            const imageURI = canvas.toDataURL("image/png");
            const a = document.createElement("a");
            a.href = imageURI;
            a.download = filename;
            a.click();
            this.showToast("Chart exported successfully.", "success");
        } catch (e) {
            this.showToast("Failed to export chart image: " + e.message, "error");
        }
    },

    showToast(message, type = "info") {
        let container = document.getElementById("toast-container");
        if (!container) {
            const target = document.querySelector(".app-container") || document.body;
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "toast-container";
            target.appendChild(container);
        }

        const toast = document.createElement("div");
        toast.className = `toast ${type}`;

        let icon = "fa-info-circle";
        if (type === "success") icon = "fa-check-circle";
        if (type === "error") icon = "fa-exclamation-circle";
        if (type === "warning") icon = "fa-exclamation-triangle";

        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = "slideIn 0.3s reverse forwards";
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }
};

// ---------------------------------------------
// AI Assistant View Controller & Chat Engine
// ---------------------------------------------
function sendQuickPrompt(promptText) {
    const input = document.getElementById("chat-input");
    if (input) {
        input.value = promptText;
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const container = document.getElementById("chat-messages-container");
    if (!input || !container) return;

    const message = input.value.trim();
    if (!message) return;

    // Append user message bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerHTML = `
        <div class="chat-avatar"><i class="fas fa-user"></i></div>
        <div class="chat-content">
            <div class="chat-sender">You</div>
            <div class="chat-text">${escapeHtml(message)}</div>
        </div>
    `;
    container.appendChild(userBubble);
    input.value = "";
    container.scrollTop = container.scrollHeight;

    // Show typing indicator
    const typingBubble = document.createElement("div");
    typingBubble.className = "chat-bubble assistant typing";
    typingBubble.id = "chat-typing-indicator";
    typingBubble.innerHTML = `
        <div class="chat-avatar"><i class="fas fa-robot"></i></div>
        <div class="chat-content">
            <div class="chat-sender">AI Copilot</div>
            <div class="chat-text"><i>Analysing database query...</i></div>
        </div>
    `;
    container.appendChild(typingBubble);
    container.scrollTop = container.scrollHeight;

    try {
        const res = await API.request("/assistant/chat", {
            method: "POST",
            body: JSON.stringify({ message })
        });

        // Remove typing indicator
        const typingEl = document.getElementById("chat-typing-indicator");
        if (typingEl) typingEl.remove();

        // Render assistant response bubble
        const botBubble = document.createElement("div");
        botBubble.className = "chat-bubble assistant";

        let htmlContent = `<div class="chat-text">${formatMarkdownText(res.reply)}</div>`;

        if (res.query_used && res.query_used !== "None") {
            htmlContent += `
                <div style="margin-top: 8px; font-size: 11px; background: rgba(15,23,42,0.6); color: #38bdf8; padding: 6px 12px; border-radius: 6px; font-family: monospace;">
                    <i class="fas fa-code"></i> ${escapeHtml(res.query_used)}
                </div>
            `;
        }

        if (res.data && res.data.length > 0) {
            htmlContent += renderDataArrayTable(res.data);
        }

        botBubble.innerHTML = `
            <div class="chat-avatar"><i class="fas fa-robot"></i></div>
            <div class="chat-content">
                <div class="chat-sender">AI Copilot</div>
                ${htmlContent}
            </div>
        `;

        container.appendChild(botBubble);
        container.scrollTop = container.scrollHeight;

    } catch (err) {
        const typingEl = document.getElementById("chat-typing-indicator");
        if (typingEl) typingEl.remove();

        const errBubble = document.createElement("div");
        errBubble.className = "chat-bubble assistant";
        errBubble.innerHTML = `
            <div class="chat-avatar"><i class="fas fa-robot" style="color:var(--danger-color);"></i></div>
            <div class="chat-content">
                <div class="chat-sender">AI Copilot</div>
                <div class="chat-text" style="color:var(--danger-color);">Sorry, I encountered an error answering your question: ${escapeHtml(err.message)}</div>
            </div>
        `;
        container.appendChild(errBubble);
        container.scrollTop = container.scrollHeight;
    }
}

function initAiAssistantView(appInstance) {
    const sendBtn = document.getElementById("chat-send-btn");
    const input = document.getElementById("chat-input");

    if (sendBtn && !sendBtn.dataset.hasListener) {
        sendBtn.dataset.hasListener = "true";
        sendBtn.addEventListener("click", () => sendChatMessage());
    }

    if (input && !input.dataset.hasListener) {
        input.dataset.hasListener = "true";
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
}

function escapeHtml(str) {
    return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function formatMarkdownText(text) {
    if (!text) return "";
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
}

function renderDataArrayTable(data) {
    if (!data || data.length === 0) return "";
    const keys = Object.keys(data[0]);
    
    let html = `<div style="overflow-x:auto; margin-top:10px;"><table class="table" style="font-size:11.5px;"><thead><tr>`;
    keys.forEach(k => {
        html += `<th>${escapeHtml(k.replace(/_/g, " ").toUpperCase())}</th>`;
    });
    html += `</tr></thead><tbody>`;

    data.forEach(row => {
        html += `<tr>`;
        keys.forEach(k => {
            let val = row[k];
            if (typeof val === "number") {
                val = val > 100 ? (k.includes("sales") || k.includes("revenue") || k.includes("profit") ? `₹${val.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}` : val.toLocaleString()) : val;
            }
            html += `<td>${escapeHtml(val)}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table></div>`;
    return html;
}

// ---------------------------------------------
// Settings View Controller
// ---------------------------------------------
function initSettingsView(appInstance) {
    const companyInput = document.getElementById("settings-company-input");
    const sectorSelect = document.getElementById("settings-sector-select");
    const form = document.getElementById("settings-profile-form");
    const sampleBtn = document.getElementById("settings-download-sample-btn");
    const sampleSectorSelect = document.getElementById("settings-sample-sector");
    const resetBtn = document.getElementById("settings-reset-data-btn");

    if (appInstance.currentUser) {
        if (companyInput) companyInput.value = appInstance.currentUser.company_name || "";
        if (sectorSelect && appInstance.currentUser.business_category) {
            sectorSelect.value = appInstance.currentUser.business_category;
        }
    }

    if (form && !form.dataset.hasListener) {
        form.dataset.hasListener = "true";
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const company = companyInput ? companyInput.value.trim() : "";
            const sector = sectorSelect ? sectorSelect.value : "grocery";

            try {
                appInstance.showLoader("Updating profile settings...");
                const formData = new FormData();
                formData.append("company_name", company);
                formData.append("business_category", sector);

                const updated = await API.request("/settings/profile", {
                    method: "PUT",
                    body: formData
                });

                appInstance.currentUser = updated;
                appInstance.updateUserProfileUI(updated);
                appInstance.showToast("Company profile updated successfully.", "success");
            } catch (err) {
                appInstance.showToast(err.message || "Failed to update profile settings.", "error");
            } finally {
                appInstance.hideLoader();
            }
        });
    }

    if (sampleBtn && sampleSectorSelect) {
        sampleBtn.onclick = () => {
            const sector = sampleSectorSelect.value || "grocery";
            window.location.href = `${window.location.origin}/api/settings/sample?sector=${encodeURIComponent(sector)}`;
            appInstance.showToast(`Downloading sample ${sector.toUpperCase()} dataset...`, "info");
        };
    }

    if (resetBtn) {
        resetBtn.onclick = async () => {
            if (confirm("Are you sure you want to wipe all uploaded datasets and reset ML models for this tenant?")) {
                try {
                    appInstance.showLoader("Resetting tenant datasets...");
                    await API.request("/settings/reset", { method: "POST" });
                    appInstance.showToast("Datasets and models reset successfully.", "success");
                } catch (err) {
                    appInstance.showToast(err.message || "Failed to reset data.", "error");
                } finally {
                    appInstance.hideLoader();
                }
            }
        };
    }
}
