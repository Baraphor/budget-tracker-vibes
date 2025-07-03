let categoryChart, subcategoryChart, fullSubcategoryData = {};
let incomeExpenseChart = null;

function clearSubcategoryChart() {
  if (subcategoryChart) {
    subcategoryChart.destroy();
    subcategoryChart = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadCharts();
});

function populateMonthOptions(months) {
  const dropdown = document.getElementById("monthGraphFilter");
  dropdown.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "";
  allOption.textContent = "All Months";
  dropdown.appendChild(allOption);

  months.forEach(month => {
    const option = document.createElement("option");
    option.value = month;
    option.textContent = month;
    dropdown.appendChild(option);
  });
}

function loadCharts() {
  const month = document.getElementById("monthGraphFilter").value;
  const payload = month === "all" ? {} : { month };

  fetch("/graphs/get/monthly", {
    method: "POST",
    headers: { "Content-Type": "application/json", 'X-Session-Token': SESSION_TOKEN },
    body: JSON.stringify(payload)
  })
  .then(res => res.json().then(body => ({ status: res.status, body })))
  .then(({ status, body }) => {
    if (status === 200) {
      fullSubcategoryData = body.subcategory_totals || {};
      renderCategoryChart(body.category_totals);
      clearSubcategoryChart();
    } else {
      showToast(body.error || "Failed to load charts.", "error");
    }
  })
  .catch(() => showToast("An error occurred loading charts.", "error"));
}

function generateColors(count) {
  const colors = [];
  const hueStep = 360 / count;
  for (let i = 0; i < count; i++) {
    const hue = i * hueStep;
    colors.push(`hsl(${hue}, 70%, 60%)`);
  }
  return colors;
}

function renderCategoryChart(data) {
  const ctx = document.getElementById("categoryGraph").getContext("2d");
  if (categoryChart) categoryChart.destroy();

  const labels = Object.keys(data);
  const amounts = Object.values(data);

  categoryChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [{
        label: "Amount",
        data: amounts,
        backgroundColor: generateColors(labels.length),
      }]
    },
    options: {
      onClick: function (e, elements) {
        if (elements.length > 0) {
          const clickedIndex = elements[0].index;
          const category = labels[clickedIndex];
          const subData = fullSubcategoryData[category];
          if (subData) {
            renderSubcategoryChart(subData);
          } else {
            clearSubcategoryChart();
          }
        }
      },
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: $${context.raw.toFixed(2)}`;
            }
          }
        },
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

function renderSubcategoryChart(data) {
  const ctx = document.getElementById("subcategoryGraph").getContext("2d");
  if (subcategoryChart) subcategoryChart.destroy();

  const labels = Object.keys(data);
  const amounts = Object.values(data);

  subcategoryChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [{
        label: "Amount",
        data: amounts,
        backgroundColor: generateColors(labels.length),
      }]
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || "";
              const value = context.raw || 0;
              return `${label}: $${value.toFixed(2)}`;
            }
          }
        },
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

function renderIncomeExpenseChart(data) {
  const labels = data.map(entry => entry.month);
  const incomes = data.map(entry => entry.income);
  const expenses = data.map(entry => Math.abs(entry.expenses));

  const ctx = document.getElementById("incomeExpenseChart").getContext("2d");
  if (incomeExpenseChart) incomeExpenseChart.destroy();

  incomeExpenseChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Income',
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          data: incomes
        },
        {
          label: 'Expenses',
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
          data: expenses
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: $${context.raw.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

fetch("/graphs/get/summary", {
  headers: { 'X-Session-Token': SESSION_TOKEN }
})
.then(res => res.json().then(body => ({ status: res.status, body })))
.then(({ status, body }) => {
  if (status === 200) {
    renderIncomeExpenseChart(body);
  } else {
    showToast(body.error || "Failed to load income/expense summary.", "error");
  }
})
.catch(() => showToast("An error occurred loading income/expense summary.", "error"));

// On page load
const savedMonth = localStorage.getItem('selectedGraphMonth');
if (savedMonth) {
    $('#monthGraphFilter').val(savedMonth);
    selectedMonth = savedMonth; 
}

// On change
$('#monthGraphFilter').on('change', function() {
    selectedMonth = $(this).val();
    localStorage.setItem('selectedGraphMonth', selectedMonth);
});