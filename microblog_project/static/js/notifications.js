document.addEventListener("DOMContentLoaded", () => {
    const bell = document.getElementById("notificationBell");
    const popup = document.getElementById("notificationPopup");

    if (!bell || !popup) return;

    bell.addEventListener("click", async (e) => {
        e.stopPropagation();

        const isOpen = popup.classList.toggle("show");

        if (!isOpen) return;

        // 1️⃣ Mark notifications as read (BACKEND)
        await fetch("/notifications/mark-read/");

        // 2️⃣ Remove badge immediately (FRONTEND)
        const countEl = document.querySelector(".notification-count");
        if (countEl) {
            countEl.remove(); // better than display:none
        }

        // 3️⃣ Load dropdown content
        const res = await fetch("/notifications/dropdown/");
        const data = await res.json();
        popup.innerHTML = data.html;
    });

    // Close on outside click
    document.addEventListener("click", () => {
        popup.classList.remove("show");
    });
});
