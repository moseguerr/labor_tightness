// Drag-and-drop ranking using SortableJS (loaded via CDN in ranking template)
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('ranking-container');
    if (!container) return;

    const sortable = Sortable.create(container, {
        animation: 200,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        onEnd: function() {
            updateRankNumbers();
            updateHiddenField();
        }
    });

    function updateRankNumbers() {
        container.querySelectorAll('.posting-drag-card').forEach(function(card, i) {
            card.querySelector('.rank-number').textContent = (i + 1);
        });
    }

    function updateHiddenField() {
        const names = [];
        container.querySelectorAll('.posting-drag-card').forEach(function(card) {
            names.push(card.dataset.condition);
        });
        document.getElementById('ranking-order-input').value = names.join(',');
    }

    // Initialize
    updateRankNumbers();
    updateHiddenField();
});
