document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("modalGanho");
    const btnAbrir = document.getElementById("btnAbrirModal");
    const btnFechar = document.getElementById("btnFecharModal");
    const form = document.getElementById("formGanho");

    // =========================
    // MODAL
    // =========================
    btnAbrir.onclick = () => {
        modal.classList.add("ativo");
        document.body.style.overflow = "hidden";
    };

    btnFechar.onclick = fecharModal;

    function fecharModal() {
        modal.classList.remove("ativo");
        document.body.style.overflow = "auto";
    }

    modal.addEventListener("click", (e) => {
        if (e.target === modal) fecharModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") fecharModal();
    });

    // =========================
    // CREATE
    // =========================
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        const res = await fetch("/ganhos", {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        const data = await res.json();

        if (data.success) {
            fecharModal();
            location.reload();
        }
    });

    // =========================
    // DELETE
    // =========================
    document.addEventListener("click", async (e) => {
        if (e.target.classList.contains("btn-delete")) {

            const id = e.target.dataset.id;
            const item = e.target.closest(".ganho-item");

            if (!confirm("Excluir ganho?")) return;

            const res = await fetch(`/ganhos/deletar/${id}`, {
                method: "DELETE"
            });

            const data = await res.json();

            if (data.success) {
                item.style.opacity = "0";
                item.style.transform = "translateX(50px)";
                setTimeout(() => item.remove(), 300);
            }
        }
    });

    // =========================
    // EDITAR DESCRIÇÃO
    // =========================
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("editavel")) {
            editarDescricao(e.target);
        }
    });

    function editarDescricao(el) {
        const id = el.dataset.id;
        const valorAtual = el.innerText;

        const input = document.createElement("input");
        input.value = valorAtual;

        el.replaceWith(input);
        input.focus();

        input.addEventListener("blur", async () => {
            const novo = input.value;

            await fetch(`/ganhos/editar/${id}`, {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ descricao: novo })
            });

            const strong = document.createElement("strong");
            strong.className = "editavel";
            strong.dataset.id = id;
            strong.innerText = novo;

            input.replaceWith(strong);
        });
    }

    // =========================
    // EDITAR VALOR
    // =========================
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("editavel-valor")) {
            editarValor(e.target);
        }
    });

    function editarValor(el) {
        const id = el.dataset.id;
        const atual = el.innerText.replace("R$", "").trim();

        const input = document.createElement("input");
        input.type = "number";
        input.value = atual;

        el.replaceWith(input);
        input.focus();

        input.addEventListener("blur", async () => {
            const novo = parseFloat(input.value);

            await fetch(`/ganhos/editar/${id}`, {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ valor: novo })
            });

            const div = document.createElement("div");
            div.className = "valor editavel-valor";
            div.dataset.id = id;
            div.innerText = "R$ " + novo.toFixed(2);

            input.replaceWith(div);
        });
    }

});