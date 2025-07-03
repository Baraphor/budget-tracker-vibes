// Store callback on the global window object
window.setTotalModalCallback = null;

function openSetTotalModal(categoryId, callback, currentTotal = 0) {
    $('#setTotalModal').data('category-id', categoryId).modal('show');
    $('#setTotalAmount').val(currentTotal);
    window.setTotalModalCallback = callback;
}

function confirmSetTotal() {
    const categoryId = $('#setTotalModal').data('category-id');
    const amount = parseFloat($('#setTotalAmount').val());

    if (isNaN(amount)) {
        showToast('Please enter a valid amount.', 'error');
        return;
    }

    $('#setTotalModal').modal('hide');

    if (typeof window.setTotalModalCallback === 'function') {
        console.log("Calling callback with:", categoryId, amount);
        window.setTotalModalCallback(categoryId, amount);
    } else {
        console.warn("Callback missing or invalid.");
    }

    window.setTotalModalCallback = null;
}

window.openSetTotalModal = openSetTotalModal;
window.confirmSetTotal = confirmSetTotal;
