document.addEventListener("DOMContentLoaded", () => {
    const bell = document.getElementById("notificationBell");
    const popup = document.getElementById("notificationPopup");

    if (!bell || !popup) return;

    bell.addEventListener("click", async (e) => {
        e.stopPropagation();

        const isOpen = popup.classList.toggle("show");
        if (!isOpen) return;

        await fetch("/notifications/mark-read/");

        const countEl = document.querySelector(".notification-count");
        if (countEl) countEl.remove();

        const res = await fetch("/notifications/dropdown/");
        const data = await res.json();
        popup.innerHTML = data.html;
    });

    document.addEventListener("click", () => {
        popup.classList.remove("show");
    });
});
