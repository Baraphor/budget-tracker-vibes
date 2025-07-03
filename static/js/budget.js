function updateParentValues(parentId) {
    let totalBudget = 0;
    let totalSpent = 0;

    $(`.budget-row[data-parent-id='${parentId}']`).each(function () {
        const budgetInput = $(this).find('.budget-input').val();
        const spentText = $(this).find('.budget-cell').eq(3).text().replace('$', '');

        const budget = parseFloat(budgetInput) || 0;
        const spent = parseFloat(spentText) || 0;

        totalBudget += budget;
        totalSpent += spent;
    });

    const parentRow = $(`.budget-row[data-category-id='${parentId}']`);

    parentRow.find('.budget-cell').eq(1).html(`<b>$${totalBudget.toFixed(2)}</b>`);
    parentRow.find('.budget-cell').eq(3).text(`$${totalSpent.toFixed(2)}`);

    const diff = totalBudget - totalSpent;
    const diffCell = parentRow.find('.budget-cell').eq(4);
    diffCell.text(`$${diff.toFixed(2)}`);

    applyDiffHighlight(parentRow, diff);
    calculateBudgetTotals();
}

function applyDiffHighlight(row, diff) {
    row.removeClass('row-success row-warning row-danger');
    if (diff >= 10) row.addClass('row-success');
    else if (diff >= 0) row.addClass('row-warning');
    else row.addClass('row-danger');
}

function updateBudget(input) {
    const row = $(input).closest('.budget-row');
    const categoryId = row.data('category-id');
    const parentId = row.data('parent-id');
    const budgetValue = $(input).val();

    saveBudgetValue(categoryId, budgetValue);

    if (parentId) {
        updateParentValues(parentId);
    }
}

function saveBudgetValue(categoryId, value, showMessage = true) {
    console.log("Saving budget for:", categoryId, "Value:", value);

    $.ajax({
        url: '/budget/update',
        method: 'POST',
        contentType: 'application/json',
        headers: { 'X-Session-Token': SESSION_TOKEN },
        data: JSON.stringify({ category_id: categoryId, amount: parseFloat(value) }),
        success: function () {
            console.log(`Budget saved for category ${categoryId}`);
            if (showMessage) {
                showToast('Budget updated successfully.', 'success');
            }
            calculateBudgetTotals();
        },
        error: function (xhr) {
            let msg = "Error saving budget value.";
            try {
                const response = JSON.parse(xhr.responseText);
                if (response && response.error) msg = response.error;
            } catch (_) { }
            showToast(msg, 'error');
        }
    });
}



$(document).on('click', '.toggle-arrow', function () {
    const parentRow = $(this).closest('.budget-row');
    const categoryId = parentRow.data('category-id');
    const arrow = $(this);
    const children = $(`.budget-row[data-parent-id='${categoryId}']`);
    const isVisible = children.is(':visible');

    if (isVisible) {
        children.addClass('d-none');
        arrow.removeClass('bi-chevron-down').addClass('bi-chevron-right');
    } else {
        children.removeClass('d-none');
        arrow.removeClass('bi-chevron-right').addClass('bi-chevron-down');
    }
});

$('#budgetMonth').on('change', function () {
    const selectedMonth = $(this).val();
    window.location.href = `/budget?month=${encodeURIComponent(selectedMonth)}`;
});

function setParentBudget(parentId) {
    const parentRow = $(`.budget-row[data-category-id='${parentId}']`);
    const totalBudgetText = parentRow.find('.budget-cell').eq(1).text().replace('$', '');
    const totalBudget = parseFloat(totalBudgetText) || 0;

    openSetTotalModal(parentId, function (categoryId, amount) {
        console.log("Modal confirmed for:", categoryId, "Amount:", amount);

        const children = $(`.budget-row[data-parent-id='${categoryId}']`);
        const childCount = children.length;
        if (childCount === 0) return;

        const dividedAmount = (amount / childCount).toFixed(2);

        children.each(function () {
            $(this).find('.budget-input').val(dividedAmount);
            saveBudgetValue($(this).data('category-id'), dividedAmount, false); // Suppress per-child toasts
        });

        updateParentValues(categoryId);
        calculateBudgetTotals();
        showToast("Budget amount updated.", "success");
    }, totalBudget);
}


function calculateBudgetTotals() {
    let totalBudget = 0;
    let totalSpent = 0;

    document.querySelectorAll('.budget-row').forEach(row => {
        if (row.classList.contains('parent-row')) return;

        const budget = parseFloat(row.querySelector('.budget-input')?.value || row.querySelector('b')?.textContent.replace('$', '') || 0);
        const spent = parseFloat(row.querySelectorAll('.budget-cell')[3]?.textContent.replace('$', '') || 0);

        totalBudget += isNaN(budget) ? 0 : budget;
        totalSpent += isNaN(spent) ? 0 : spent;
    });

    const totalDiff = totalBudget - totalSpent;

    document.getElementById('totalBudget').textContent = `$${totalBudget.toFixed(2)}`;
    document.getElementById('totalSpent').textContent = `$${totalSpent.toFixed(2)}`;
    document.getElementById('totalDiff').textContent = `$${totalDiff.toFixed(2)}`;
}

const savedMonth = localStorage.getItem('selectedBudgetMonth');
if (savedMonth) {
    $('#budgetMonth').val(savedMonth);
    selectedMonth = savedMonth; 
}

// On change
$('#budgetMonth').on('change', function() {
    selectedMonth = $(this).val();
    localStorage.setItem('selectedBudgetMonth', selectedMonth);
});