function addTransaction() {
  const accountType = document.getElementById("accountType").value;
  const transactionDate = document.getElementById("transactionDate").value;
  const description = document.getElementById("description").value.trim();
  const amount = parseFloat(document.getElementById("amount").value);
  const category = document.getElementById("category").value;

  if (!accountType || !transactionDate || !description || isNaN(amount) || !category) {
    showToast('Please fill all fields with valid values.', 'error');
    return;
  }

  const data = {
    account_type: accountType,
    transaction_date: transactionDate,
    description: description,
    amount: amount,
    category: category
  };

  fetch('/transaction/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Token': SESSION_TOKEN },
    body: JSON.stringify(data)
  })
  .then(res => res.json().then(body => ({ status: res.status, body })))
  .then(({ status, body }) => {
    if (status === 200) {
      $('#transactionTable').bootstrapTable('refresh', { silent: true });
      clearTransactionForm();
      showToast('Transaction added successfully.', 'success');
    } else {
      showToast(body.error || 'Failed to add transaction.', 'error');
    }
  })
  .catch(() => {
    showToast('Failed to add transaction.', 'error');
  });
}

function assignCategory(transactionId, categoryId) {
  fetch("/transaction/update/category", {
    method: "POST",
    headers: { "Content-Type": "application/json", 'X-Session-Token': SESSION_TOKEN },
    body: JSON.stringify({
      transaction_id: transactionId,
      category_id: parseInt(categoryId)
    })
  })
  .then(res => {
    if (res.status === 204) {
      $('#transactionTable').bootstrapTable('refresh', { silent: true });
      showToast('Category updated successfully.', 'success');
    } else {
      return res.json().then(body => {
        showToast(body.error || 'Failed to update category.', 'error');
      });
    }
  })
  .catch(() => {
    showToast('Category update failed.', 'error');
  });
}


function enableDescriptionEdit(spanElement, rowId) {
  const container = spanElement.parentElement;
  const input = container.querySelector("input");

  input.value = spanElement.textContent;
  spanElement.classList.add("d-none");
  input.classList.remove("d-none");
  input.focus();
}

function saveDescriptionEdit(inputElement, rowId) {
  const newValue = inputElement.value.trim();
  const container = inputElement.parentElement;
  const span = container.querySelector(".description-text");

  fetch("/transaction/update/description", {
      method: "POST",
      headers: { "Content-Type": "application/json", 'X-Session-Token': SESSION_TOKEN },
      body: JSON.stringify({ id: rowId, description: newValue })
  })
  .then(res => {
      if (res.status === 204) {
          $('#transactionTable').bootstrapTable('refresh', { silent: true });
          showToast('Description updated.', 'success');
      } else {
          return res.json().then(body => {
              showToast(body.error || 'Failed to update description.', 'error');
          });
      }
  })
  .catch(() => {
      showToast('Server error occurred.', 'error');
  });

}

function clearTransactionForm() {
  document.getElementById("accountType").value = "";
  document.getElementById("transactionDate").value = "";
  document.getElementById("description").value = "";
  document.getElementById("amount").value = "";
  document.getElementById("category").value = "";
}

function amountFormatter(value) {
  const num = parseFloat(value);
  return isNaN(num) ? "$0.00" : `$${num.toFixed(2)}`;
}

function totalAmountFormatter(data) {
  const total = data.reduce((sum, row) => {
    const amount = parseFloat(row.amount);
    return sum + (isNaN(amount) ? 0 : amount);
  }, 0);
  return `$${total.toFixed(2)}`;
}

function categoryFormatter(value, row) {
  let html = `<select class="form-select form-select-sm" onchange="assignCategory(${row.id}, this.value)">`;

  categories.forEach(cat => {
    const selected = cat.id === row.category ? "selected" : "";
    html += `<option value="${cat.id}" ${selected}>${cat.name}</option>`;

    (cat.subcategories || []).forEach(sub => {
      const subSelected = sub.id === row.category ? "selected" : "";
      html += `<option value="${sub.id}" ${subSelected}>&nbsp;&nbsp;&#10551; ${sub.name}</option>`;
    });
  });

  html += "</select>";
  return html;
}

function actionFormatter(value, row) {
  return `
    <button class="btn btn-sm btn-danger delete-transaction" title="Delete">
      <i class="bi bi-trash"></i>
    </button>
  `;
}

function descriptionFormatter(value, row) {
  return `
    <span class="description-text" ondblclick="enableDescriptionEdit(this, ${row.id})">${value}</span>
    <input type="text" class="form-control form-control-sm d-none"
           onblur="saveDescriptionEdit(this, ${row.id})"
           onkeydown="if(event.key === 'Enter'){ event.preventDefault(); this.blur(); }" />
  `;
}

window.actionEvents = {
  'click .delete-transaction': function (e, value, row) {
    showConfirmModal("Confirm Delete", "Are you sure you want to delete this transaction?", "Delete", () => {
      fetch(`/transaction/delete/${row.id}`, { method: 'DELETE', headers: { 'X-Session-Token': SESSION_TOKEN } })
        .then(res => {
          if (res.status === 204) {
            $('#transactionTable').bootstrapTable('refresh', { silent: true });
            showToast('Transaction deleted', 'success');
          } else {
            return res.json().then(body => {
              showToast(body.error || 'Failed to delete transaction.', 'error');
            });
          }
        })
        .catch(() => {
          showToast('An error occurred while deleting the transaction.', 'error');
        });
    });
  }
};


function loadMonthOptions() {
  fetch("/transactions/get/months", { method: 'GET', headers: { 'X-Session-Token': SESSION_TOKEN } })
    .then(res => res.json())
    .then(months => {
      const select = document.getElementById("monthFilter");
      select.innerHTML = "";  // Optional: clear existing options

      const optAll = document.createElement("option");
      optAll.value = "all";
      optAll.textContent = "All";
      select.appendChild(optAll);

      months.forEach(month => {
        const opt = document.createElement("option");
        opt.value = month;
        opt.textContent = month;
        select.appendChild(opt);
      });

      // Now apply localStorage value
      const savedMonth = localStorage.getItem('selectedMonthFilter');
      if (savedMonth && months.includes(savedMonth)) {
        select.value = savedMonth;
        selectedMonth = savedMonth;
      } else {
        selectedMonth = "all";
      }

      $('#transactionTable').bootstrapTable('refresh');
    });
}


document.addEventListener("DOMContentLoaded", function () {
  const table = document.getElementById("transactionTable");
  const spinner = document.getElementById("loadingSpinner");

  if (table && spinner) {
    setTimeout(() => {
      $('#transactionTable').bootstrapTable('resetView');
      spinner.classList.add("d-none");
      table.classList.remove("d-none");
    }, 150);
  }
});

// Drag and drop file upload support
const dropArea = document.getElementById('drop-area');
dropArea.addEventListener('dragover', e => {
  e.preventDefault();
  dropArea.classList.add('bg-light');
});
dropArea.addEventListener('dragleave', () => {
  dropArea.classList.remove('bg-light');
});
dropArea.addEventListener('drop', e => {
  e.preventDefault();
  dropArea.classList.remove('bg-light');
  const file = e.dataTransfer.files[0];
  if (!file.name.endsWith('.csv')) {
    showToast('Please drop a .csv file.', 'error');
    return;
  }
  const formData = new FormData();
  formData.append('csv_file', file);
  fetch('/upload', {
    method: 'POST',
    headers: { 'X-Session-Token': SESSION_TOKEN },
    body: formData
  })
  .then(res => res.json().then(body => ({ status: res.status, body })))
  .then(({ status, body }) => {
    if (status === 200) {
      showToast('File uploaded successfully.', 'success');
      window.location.reload();
    } else {
      showToast(body.error || 'Upload failed.', 'error');
    }
  })
  .catch(() => {
    showToast('Upload failed.', 'error');
  });
});

// On change
$('#monthFilter').on('change', function() {
    selectedMonth = $(this).val();
    localStorage.setItem('selectedMonthFilter', selectedMonth);
    $('#transactionTable').bootstrapTable('refresh', { silent: true });
});