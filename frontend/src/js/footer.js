async function loadFooter(path) {
    try {
        const response = await fetch(path);
        const data = await response.text();
        const footerContainer = document.getElementById('footer');
        if (footerContainer) {
            footerContainer.innerHTML = data;
        }
    } catch (error) {
        console.error('Error loading footer:', error);
    }
}