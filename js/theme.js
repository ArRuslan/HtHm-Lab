function setTheme(theme_name) {
    localStorage.setItem('theme', theme_name);
    document.body.className = `theme-${theme_name}`;
}

function toggleTheme() {
    if (localStorage.getItem('theme') === 'light') {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}