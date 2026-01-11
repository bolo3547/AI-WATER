// Suppress harmless AbortError from Plotly animations
window.addEventListener('unhandledrejection', function(event) {
  try {
    if (event && event.reason && event.reason.name === 'AbortError') {
      event.preventDefault();
    }
  } catch (e) {
    // ignore
  }
});
