document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("add-category-form");

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const name = document.getElementById("category-name").value.trim();
        const parentId = document.getElementById("parent-category").value || null;

        if (!name) return;

        fetch("/categories/add", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                'X-Session-Token': SESSION_TOKEN
             },
            body: JSON.stringify({ name, parent_id: parentId })
        })
        .then(res => {
            if (res.ok) {
                location.reload();
            } else {
                showMessageModal("Failed to add category.", "Add Category Failed");
            }
        })
        .catch(() => showMessageModal("Server error adding category.", "Add Category Failed"));
    });
});
