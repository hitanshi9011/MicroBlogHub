document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("togglePassword");
    const password = document.getElementById("password");
    const icon = toggle.querySelector("i");
  
    toggle.addEventListener("click", () => {
      if (password.type === "password") {
        password.type = "text";
        icon.classList.replace("fa-eye", "fa-eye-slash");
      } else {
        password.type = "password";
        icon.classList.replace("fa-eye-slash", "fa-eye");
      }
    });
  });
  