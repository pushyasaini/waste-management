// ===============================
// GHMC System JavaScript
// ===============================

console.log("GHMC Waste Management System Loaded");

// Confirm before deleting
function confirmAction(message) {
    return confirm(message);
}

// Auto-hide alerts
window.onload = function() {
    const alerts = document.querySelectorAll(".alert");
    setTimeout(() => {
        alerts.forEach(alert => alert.style.display = "none");
    }, 4000);
};

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
}