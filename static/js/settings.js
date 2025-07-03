document.addEventListener("DOMContentLoaded", () => {
  const deleteBtn = document.getElementById("triggerDeleteAllBtn");

  if (deleteBtn) {
    deleteBtn.addEventListener("click", () => {
      showConfirmModal("Confirm Delete", "Are you sure you want to delete all transactions?", "Delete", () => {
        fetch("/settings/clear-transactions", {
          method: "DELETE",
          headers: { 'X-Session-Token': SESSION_TOKEN }
        })
        .then(res => {
          if (res.ok) {
            showToast("All transactions deleted.", "success");
          } else {
            res.json().then(body => {
              showToast(body.error || "Failed to delete transactions.", "error");
            }).catch(() => {
              showToast("Failed to delete transactions.", "error");
            });
          }
        })
        .catch(() => {
          showToast("An error occurred while deleting transactions.", "error");
        });
      });
    });
  }
});
