// Time-on-page tracking
(function() {
    const pageLoadTime = new Date().toISOString();

    // Store page load timestamp in a hidden field if present
    const timestampField = document.querySelector('input[name="displayed_at"]');
    if (timestampField) {
        timestampField.value = pageLoadTime;
    }

    // Track time spent before form submission
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            const respondedField = form.querySelector('input[name="responded_at"]');
            if (respondedField) {
                respondedField.value = new Date().toISOString();
            }
        });
    });
})();
