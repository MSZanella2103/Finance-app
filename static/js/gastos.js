document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("modalGasto");
    const btnAbrir = document.getElementById("btnAbrirModal");
    const btnFechar = document.getElementById("btnFecharModal");
    const form = document.getElementById("formGasto");
    

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
    // AJAX FORM
    // =========================
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        try {
            const res = await fetch("/gastos", {
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

        } catch (err) {
            console.error(err);
        }
    });

    // =========================
    // DELETE
    // =========================
    document.addEventListener("click", async (e) => {
        if (e.target.classList.contains("btn-delete")) {
            const id = e.target.dataset.id;
            const item = e.target.closest(".gasto-item");

            if (!confirm("Excluir gasto?")) return;

            const res = await fetch(`/gastos/deletar/${id}`, {
                method: "DELETE"
            });

            const data = await res.json();

            if (data.success) {
                item.style.opacity = "0";
                item.style.transform = "translateX(50px)";
                setTimeout(() => item.remove(), 300);

                toast("Removido 🗑️");
            }
        }
    });

    // =========================
    // EDITAR
    // =========================
    document.addEventListener("click", (e) => {
        if (e.target.closest(".editavel")) {
            editar(e.target.closest(".editavel"));
        }
    });

    function editar(el) {
        const id = el.dataset.id;
        const valorAtual = el.innerText;

        const input = document.createElement("input");
        input.value = valorAtual;

        el.replaceWith(input);
        input.focus();

        input.addEventListener("blur", async () => {
            const novo = input.value;

            await fetch(`/gastos/editar/${id}`, {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    descricao: novo
                })
            });

            const strong = document.createElement("strong");
            strong.className = "editavel";
            strong.dataset.id = id;
            strong.innerText = novo;

            input.replaceWith(strong);

            toast("Atualizado ✏️");
        });
    }

});

// =========================
// HELPERS
// =========================


function toast(msg) {
    const t = document.createElement("div");
    t.className = "toast";
    t.innerText = msg;

    document.body.appendChild(t);

    setTimeout(() => t.classList.add("show"), 100);
    setTimeout(() => t.remove(), 3000);
}

// =========================
// TOGGLE PAGO
// =========================
document.addEventListener("click", async (e) => {
    if (e.target.classList.contains("btn-toggle-pago")) {
        const id = e.target.dataset.id;

        await fetch(`/gastos/toggle_pago/${id}`);
        location.reload();
    }
});
/*
// =========================
// EDITAR DESCRIÇÃO
// =========================
function editar(el) {
    const id = el.dataset.id;
    const valorAtual = el.innerText;

    const input = document.createElement("input");
    input.value = valorAtual;

    el.replaceWith(input);
    input.focus();

    input.addEventListener("blur", async () => {
        const novo = input.value;

        await fetch(`/gastos/editar/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                descricao: novo
            })
        });

        const strong = document.createElement("strong");
        strong.className = "editavel";
        strong.dataset.id = id;
        strong.innerText = novo;

        input.replaceWith(strong);

        toast("Atualizado ✏️");
    });
}
*/

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

        await fetch(`/gastos/editar/${id}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                valor: novo
            })
        });

        const div = document.createElement("div");
        div.className = "valor editavel-valor";
        div.dataset.id = id;
        div.innerText = "R$ " + novo.toFixed(2);

        input.replaceWith(div);

        toast("Valor atualizado 💰");
    });
}


// =========================
// APARECER PRESTAÇÃO APENAS SE FOR SELECIONADO CRÉDITO
// =========================
const selectCartao = document.querySelector('[name="cartao_id"]');
const campoParcelas = document.querySelector('[name="parcelas"]');

function toggleParcelas() {
    if (selectCartao.value) {
        campoParcelas.style.display = "block";
    } else {
        campoParcelas.style.display = "none";
        campoParcelas.value = 1;
    }
}

selectCartao.addEventListener("change", toggleParcelas);
toggleParcelas();