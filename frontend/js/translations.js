window.translations = {
    "en": {
        "nav_dashboard": "Dashboard",
        "nav_analytics": "Analytics",
        "nav_leaderboard": "Leaderboard",
        "nav_admin": "Admin",
        "app_title": "JAN SAHAYAK",
        "app_subtitle": "Citizen Reporting Portal",
        "btn_new_report": "+ FILE NEW REPORT",
        "kpi_active": "Active Issues",
        "kpi_votes": "Community Votes",
        "empty_state": "No active reports. Be the first to file one.",
        "modal_title": "NEW REPORT",
        "modal_subtitle": "Submit a civic issue",
        "label_name": "Your Name",
        "placeholder_name": "Enter your name for leaderboard",
        "label_location": "Location",
        "btn_gps": "USE GPS",
        "placeholder_search": "Search location (e.g. Vikas Nagar)",
        "status_awaiting": "Awaiting input...",
        "capture_media": "Capture Image or Video",
        "label_desc": "Description",
        "placeholder_desc": "Describe the issue clearly...",
        "btn_submit": "SUBMIT REPORT",
        "toast_success": "Report submitted! +10 points",
        "toast_loc_req": "Location is required.",
        "cat_general": "General",
        "cat_pothole": "Pothole & Road",
        "cat_garbage": "Garbage & Waste",
        "cat_streetlight": "Streetlight",
        "by": "by"
    },
    "hi": {
        "nav_dashboard": "डैशबोर्ड",
        "nav_analytics": "विश्लेषण",
        "nav_leaderboard": "लीडरबोर्ड",
        "nav_admin": "प्रशासन",
        "app_title": "जन सहायक",
        "app_subtitle": "नागरिक रिपोर्टिंग पोर्टल",
        "btn_new_report": "+ नई रिपोर्ट दर्ज करें",
        "kpi_active": "सक्रिय समस्याएँ",
        "kpi_votes": "सामुदायिक वोट",
        "empty_state": "कोई सक्रिय रिपोर्ट नहीं। पहली रिपोर्ट दर्ज करें।",
        "modal_title": "नई रिपोर्ट",
        "modal_subtitle": "नागरिक समस्या दर्ज करें",
        "label_name": "आपका नाम",
        "placeholder_name": "लीडरबोर्ड के लिए अपना नाम दर्ज करें",
        "label_location": "स्थान",
        "btn_gps": "GPS का उपयोग करें",
        "placeholder_search": "स्थान खोजें (उदा. विकास नगर)",
        "status_awaiting": "इनपुट की प्रतीक्षा है...",
        "capture_media": "चित्र या वीडियो लें",
        "label_desc": "विवरण",
        "placeholder_desc": "समस्या का स्पष्ट रूप से वर्णन करें...",
        "btn_submit": "रिपोर्ट जमा करें",
        "toast_success": "रिपोर्ट जमा हो गई! +10 अंक",
        "toast_loc_req": "स्थान अनिवार्य है।",
        "cat_general": "सामान्य",
        "cat_pothole": "सड़क और गड्ढे",
        "cat_garbage": "कचरा और अपशिष्ट",
        "cat_streetlight": "स्ट्रीटलाइट",
        "by": "द्वारा"
    }
};

const translations = window.translations;

let currentLang = localStorage.getItem('janSahayakLang') || 'en';

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'hi' : 'en';
    localStorage.setItem('janSahayakLang', currentLang);
    applyTranslations();
    
    // Dispatch custom event so other components (like reports list) can re-render if needed
    window.dispatchEvent(new Event('languageChanged'));
}

function applyTranslations() {
    const t = translations[currentLang];
    if (!t) return;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = t[key];
            } else {
                el.childNodes.forEach(child => {
                    if (child.nodeType === Node.TEXT_NODE && child.textContent.trim().length > 0) {
                        child.textContent = t[key];
                    }
                });
                // If no text node was found but we want to set text (and not destroy children like spans)
                if(el.childNodes.length === 0) {
                     el.textContent = t[key];
                } else if (el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE) {
                     el.textContent = t[key];
                }
            }
        }
    });

    // Update pill nav if available
    const navItems = document.querySelectorAll('.pill-label');
    const hoverItems = document.querySelectorAll('.pill-label-hover');
    if (navItems.length >= 4) {
        navItems[0].textContent = t['nav_dashboard'];
        navItems[1].textContent = t['nav_analytics'];
        navItems[2].textContent = t['nav_leaderboard'];
        navItems[3].textContent = t['nav_admin'];
    }
    if (hoverItems.length >= 4) {
        hoverItems[0].textContent = t['nav_dashboard'];
        hoverItems[1].textContent = t['nav_analytics'];
        hoverItems[2].textContent = t['nav_leaderboard'];
        hoverItems[3].textContent = t['nav_admin'];
    }
    const mobileItems = document.querySelectorAll('.mobile-menu-link');
    if (mobileItems.length >= 4) {
        mobileItems[0].textContent = t['nav_dashboard'];
        mobileItems[1].textContent = t['nav_analytics'];
        mobileItems[2].textContent = t['nav_leaderboard'];
        mobileItems[3].textContent = t['nav_admin'];
    }

    // Update toggle button text
    const toggleBtn = document.getElementById('lang-toggle-btn');
    if (toggleBtn) {
        toggleBtn.textContent = currentLang === 'en' ? '🌐 HI' : '🌐 EN';
    }
    
    // Set Poppins font for Hindi
    if (currentLang === 'hi') {
        document.body.style.fontFamily = "'Poppins', sans-serif";
    } else {
        document.body.style.fontFamily = "";
    }
}

// Apply on load
window.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
});
