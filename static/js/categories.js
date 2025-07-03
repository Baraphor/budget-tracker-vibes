document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll('div.collapse').forEach(target => {
        const icon = document.querySelector(`.toggle-icon[data-bs-target="#${target.id}"]`);

        if (icon && target) {
            target.addEventListener("show.bs.collapse", () => icon.classList.add("rotate-down"));
            target.addEventListener("hide.bs.collapse", () => icon.classList.remove("rotate-down"));
        }
    });

    document.querySelectorAll(".delete-category").forEach(button => {
        button.addEventListener("click", (e) => {
            e.stopPropagation();

            const id = button.dataset.id;
            showConfirmModal("Confirm Delete", "Are you sure you want to delete this category?", "Delete", () => {
                fetch(`/categories/delete/${id}`, { 
                    method: "DELETE", 
                    headers: { "Content-Type": "application/json", 'X-Session-Token': SESSION_TOKEN }
                })
                .then(res => {
                    if (res.status === 204) {
                        removeCategoryElement(button, id);
                        showToast("Category deleted successfully.", "success");
                    } else {
                        return res.json().then(body => {
                            showToast(body.error || "Failed to delete category.", "error");
                        });
                    }
                })
                .catch(() => showToast("Server error deleting category.", "error"));
                        });
                    });
                });

    function removeCategoryElement(button, id) {
        const row = button.closest(".category-row, .subcategory-row");
        if (row) row.remove();

        const subSection = document.getElementById(`subcategory-${id}`);
        if (subSection) subSection.remove();

        const subcategoryRow = button.closest(".subcategory-row");
        if (subcategoryRow) {
            const parentId = subcategoryRow.querySelector(".editable")?.dataset.parent;
            const parentSubList = document.getElementById(`subcategory-${parentId}`);
            const remainingChildren = parentSubList?.querySelectorAll(".subcategory-row");

            if (!remainingChildren || remainingChildren.length === 0) {
                const parentRow = document.querySelector(`.category-row input[data-id="${parentId}"]`)?.closest(".category-row");
                const icon = parentRow?.querySelector(`.toggle-icon[data-bs-target="#subcategory-${parentId}"]`);
                const subList = document.getElementById(`subcategory-${parentId}`);

                if (icon) icon.remove();
                if (subList) subList.remove();
            }
        }
    }

    document.querySelectorAll(".editable").forEach(input => {
        input.addEventListener("blur", () => finalizeEdit(input));
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                input.blur();
            }
        });
    });

    function finalizeEdit(input) {
        input.readOnly = true;
        input.classList.add("form-control-plaintext");
        input.classList.remove("form-control");

        const id = parseInt(input.dataset.id);
        const new_name = input.value.trim();

        fetch("/categories/update", {
            method: "POST",
            headers: { "Content-Type": "application/json", 'X-Session-Token': SESSION_TOKEN },
            body: JSON.stringify({ id, new_name })
        })
        .then(res => {
            if (res.status === 204) {
                showToast("Category name updated.", "success");
            } else {
                return res.json().then(body => {
                    showToast(body.error || "Failed to update category.", "error");
                });
            }
        })
        .catch(() => {
            showToast("Server error updating category.", "error");
        });
    }
});

window.toggleBudgetInclusion = function(checkbox) {
    const categoryId = $(checkbox).data('id');

    $.ajax({
        url: `/categories/toggle_include/${categoryId}`,
        method: "POST",
        headers: { 'X-Session-Token': SESSION_TOKEN }
    })
    .done(() => {
        showToast('Budget inclusion updated successfully.', 'success');
    })
    .fail(xhr => {
        checkbox.checked = !checkbox.checked;
        const response = xhr.responseJSON;
        const msg = response?.error || "Failed to update budget inclusion. Please try again.";
        showToast(msg, 'error');
    });
}
