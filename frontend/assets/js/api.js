// Central API Utility for backend communication

const API_BASE = window.location.origin + "/api";

const API = {
    getToken() {
        return localStorage.getItem("retail_bi_token");
    },
    
    setToken(token) {
        localStorage.setItem("retail_bi_token", token);
    },
    
    removeToken() {
        localStorage.removeItem("retail_bi_token");
    },
    
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        
        // Setup headers
        const headers = options.headers || {};
        const token = this.getToken();
        
        if (token && !headers["Authorization"]) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        
        // If content-type not set and body is not FormData, default to JSON
        if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }
        
        const config = {
            ...options,
            headers
        };
        
        try {
            const response = await fetch(url, config);
            
            // Check for unauthorized access
            if (response.status === 401) {
                this.removeToken();
                // Redirect user to login page/view
                window.dispatchEvent(new CustomEvent("auth-expired"));
                throw new Error("Session expired. Please log in again.");
            }
            
            // Check if downloading binary file
            const contentType = response.headers.get("content-type");
            if (contentType && (
                contentType.includes("application/pdf") || 
                contentType.includes("spreadsheetml") || 
                contentType.includes("text/csv")
            )) {
                if (!response.ok) {
                    const errObj = await response.json();
                    throw new Error(errObj.detail || "Download failed");
                }
                return await response.blob();
            }
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "API request failed");
            }
            
            return data;
        } catch (error) {
            console.error("API Error details:", error);
            throw error;
        }
    }
};
