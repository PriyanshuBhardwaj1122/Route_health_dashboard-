/* Feedback submission form logic — star ratings + route selection */

document.addEventListener("DOMContentLoaded", async () => {
    // Load routes into dropdown
    try {
        const res = await fetch("/routes");
        const routes = await res.json();
        const select = document.getElementById("route-select");
        routes.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.id;
            opt.textContent = `Route ${r.route_number} — ${r.name}`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load routes:", err);
    }

    // Star rating interaction
    const ratings = {};
    document.querySelectorAll(".star-group").forEach(group => {
        const field = group.dataset.field;
        ratings[field] = 0;
        const stars = group.querySelectorAll(".star");

        stars.forEach(star => {
            star.addEventListener("click", () => {
                const val = parseInt(star.dataset.value);
                ratings[field] = val;
                stars.forEach(s => {
                    s.classList.toggle("active", parseInt(s.dataset.value) <= val);
                });
            });

            star.addEventListener("mouseenter", () => {
                const val = parseInt(star.dataset.value);
                stars.forEach(s => {
                    s.classList.toggle("hover", parseInt(s.dataset.value) <= val);
                });
            });

            star.addEventListener("mouseleave", () => {
                stars.forEach(s => s.classList.remove("hover"));
            });
        });
    });

    // Form submission
    const form = document.getElementById("feedback-form");
    const successMsg = document.getElementById("success-msg");
    const categoryResult = document.getElementById("category-result");
    const submitBtn = document.getElementById("submit-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        successMsg.classList.remove("show");

        const routeId = parseInt(document.getElementById("route-select").value);
        const comment = document.getElementById("comment").value.trim() || null;

        if (!routeId) {
            alert("Please select a route.");
            return;
        }

        // Check all ratings are set
        const fields = ["rating_overall", "rating_punctuality", "rating_cleanliness",
                        "rating_crowding", "rating_driver_behaviour"];
        for (const f of fields) {
            if (!ratings[f] || ratings[f] === 0) {
                alert("Please rate all categories (click the stars).");
                return;
            }
        }

        const payload = {
            route_id: routeId,
            rating_overall: ratings.rating_overall,
            rating_punctuality: ratings.rating_punctuality,
            rating_cleanliness: ratings.rating_cleanliness,
            rating_crowding: ratings.rating_crowding,
            rating_driver_behaviour: ratings.rating_driver_behaviour,
            comment: comment,
        };

        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting…";

        try {
            const res = await fetch("/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const result = await res.json();

            let catText = ` Severity: <strong>${result.severity}</strong>.`;
            if (result.category) {
                catText += ` Category: <strong>${result.category}</strong>.`;
            }
            categoryResult.innerHTML = catText;
            successMsg.classList.add("show");

            // Reset form
            form.reset();
            document.querySelectorAll(".star").forEach(s => {
                s.classList.remove("active", "hover");
            });
            Object.keys(ratings).forEach(k => ratings[k] = 0);
        } catch (err) {
            alert("Failed to submit feedback. Please try again.");
            console.error(err);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit Feedback";
        }
    });
});
