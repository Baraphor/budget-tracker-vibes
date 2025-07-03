function showToast(message, type = 'info', delay = 3000) {
    const toastId = `toast-${Date.now()}`;

    const bgClass = {
        success: 'bg-success text-white',
        error: 'bg-danger text-white',
        info: 'bg-primary text-white',
        warning: 'bg-warning text-dark'
    }[type] || 'bg-secondary text-white';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} mb-2" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${delay}">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    const container = document.getElementById('toastContainer');
    container.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}
