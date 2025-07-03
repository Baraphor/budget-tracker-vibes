function showSuccessModal(message = "Operation successful.", btnText="Close") {
  document.getElementById("genericModalHeader").className = "modal-header bg-success text-white";
  document.getElementById("genericModalTitle").textContent = "Success";
  document.getElementById("genericModalBody").textContent = message;
  document.getElementById("genericModalFooter").innerHTML = `
    <button type="button" class="btn btn-success" data-bs-dismiss="modal">${btnText}</button>
  `;
  new bootstrap.Modal(document.getElementById("genericModal")).show();
}

function showConfirmModal(title, message, confirmText, onConfirm) {
  document.getElementById("genericModalHeader").className = "modal-header";
  document.getElementById("genericModalTitle").textContent = title;
  document.getElementById("genericModalBody").textContent = message;
  document.getElementById("genericModalFooter").innerHTML = `
    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
    <button type="button" class="btn btn-danger" id="genericConfirmBtn">${confirmText}</button>
  `;
  const modal = new bootstrap.Modal(document.getElementById("genericModal"));
  modal.show();

  document.getElementById("genericConfirmBtn").onclick = () => {
    modal.hide();
    if (typeof onConfirm === "function") onConfirm();
  };
}

function showErrorModal(message = "An error occurred.", btnText = "Close") {
  document.getElementById("genericModalHeader").className = "modal-header bg-danger text-white";
  document.getElementById("genericModalTitle").textContent = "Error";
  document.getElementById("genericModalBody").textContent = message;
  document.getElementById("genericModalFooter").innerHTML = `
    <button type="button" class="btn btn-danger" data-bs-dismiss="modal">${btnText}</button>
  `;
  new bootstrap.Modal(document.getElementById("genericModal")).show();
}