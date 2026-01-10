// Opening animation controller
document.addEventListener('DOMContentLoaded', function() {
    const openingAnimation = document.getElementById('opening-animation');
    const mainContent = document.getElementById('main-content');
    
    // Play launch sound
    const launchSound = new Audio('../assets/sounds/launch_sound.wav');
    launchSound.play().catch(err => console.log('Audio play failed:', err));
    
    // After 1 second, fade out opening animation and show main content
    setTimeout(() => {
        openingAnimation.classList.add('fade-out');
        
        // Wait for fade-out transition to complete
        setTimeout(() => {
            openingAnimation.style.display = 'none';
            mainContent.classList.remove('hidden');
            mainContent.classList.add('visible');
        }, 300); // Match the CSS transition duration
    }, 1000); // 1 second animation duration
});
