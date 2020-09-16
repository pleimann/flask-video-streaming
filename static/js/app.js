var element = document.getElementById('waffleImage');
function toggleFullScreen() {
    try {
        if (!document.fullscreenElement) {
            element.requestFullscreen();

        } else if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    } catch (e) {
        window.alert('sorry unable to go to fullscreen! ' + e.message);
    }
}
