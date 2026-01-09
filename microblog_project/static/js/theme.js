// Theme toggle: toggles body.light-theme and persists to localStorage
(function(){
  function setTheme(isLight){
    if(isLight) document.documentElement.classList.add('light-theme');
    else document.documentElement.classList.remove('light-theme');
    try{ localStorage.setItem('theme', isLight ? 'light' : 'dark'); }catch(e){}
    updateIcon(isLight);
  }

  function updateIcon(isLight){
    var icon = document.getElementById('themeIcon');
    if(!icon) return;
    if(isLight){
      // sun icon
      icon.innerHTML = '<path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zM1 13h3v-2H1v2zm10-9h2V1h-2v3zm7.66 1.05l-1.41-1.41-1.8 1.79 1.42 1.42 1.79-1.8zM20 11v2h3v-2h-3zM12 7a5 5 0 100 10 5 5 0 000-10zm-1 13h2v-3h-2v3zM4.24 19.16l1.79-1.8-1.41-1.41-1.79 1.8 1.41 1.41zM18.36 19.78l1.41-1.41-1.8-1.79-1.42 1.42 1.81 1.78z" fill="#e5e7eb"/>';
    } else {
      // moon icon
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" fill="#e5e7eb"/>';
    }
  }

  document.addEventListener('DOMContentLoaded', function(){
    var toggle = document.getElementById('themeToggle');
    // initial icon
    var isLight = document.documentElement.classList.contains('light-theme');
    updateIcon(isLight);
    if(toggle){
      toggle.addEventListener('click', function(){
        var now = document.documentElement.classList.toggle('light-theme');
        try{ localStorage.setItem('theme', now ? 'light' : 'dark'); }catch(e){}
        updateIcon(now);
      });
    }
  });
})();
