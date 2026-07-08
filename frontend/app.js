const API = "";

async function createLink(url, customCode) {
  const body = { url };
  if (customCode) body.custom_code = customCode;
  const res = await fetch(`${API}/api/links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Failed to create link");
  }
  return res.json();
}

async function listLinks() {
  const res = await fetch(`${API}/api/links`);
  if (!res.ok) throw new Error("Failed to fetch links");
  return res.json();
}

async function deleteLink(code) {
  const res = await fetch(`${API}/api/links/${code}`, { method: "DELETE" });
  if (!res.ok && res.status !== 404) throw new Error("Failed to delete link");
}

function renderTable(links) {
  const tbody = document.getElementById("links-body");
  const empty = document.getElementById("empty-message");
  tbody.innerHTML = "";
  if (links.length === 0) {
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  links.forEach((link) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><a href="${link.short_url}" target="_blank">${link.short_url}</a></td>
      <td><a href="${link.url}" target="_blank">${link.url.length > 50 ? link.url.slice(0, 50) + "…" : link.url}</a></td>
      <td>${link.visit_count}</td>
      <td>${new Date(link.created_at).toLocaleDateString()}</td>
      <td><button class="delete-btn" data-code="${link.code}">Delete</button></td>
    `;
    tr.querySelector(".delete-btn").addEventListener("click", async () => {
      try {
        await deleteLink(link.code);
        await refreshTable();
      } catch (err) {
        showResult(err.message, true);
      }
    });
    tbody.appendChild(tr);
  });
}

async function refreshTable() {
  const links = await listLinks();
  renderTable(links);
}

function showResult(message, isError = false) {
  const el = document.getElementById("result");
  el.textContent = message;
  el.className = `result ${isError ? "error" : "success"}`;
}

async function handleSubmit(event) {
  event.preventDefault();
  const urlInput = document.getElementById("url-input");
  const aliasInput = document.getElementById("alias-input");
  const url = urlInput.value.trim();
  const alias = aliasInput.value.trim();

  if (!url) {
    showResult("Please enter a URL", true);
    return;
  }

  try {
    const link = await createLink(url, alias || null);
    showResult(`Short URL created: ${link.short_url}`);
    urlInput.value = "";
    aliasInput.value = "";
    await refreshTable();
  } catch (err) {
    showResult(err.message, true);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("shorten-form").addEventListener("submit", handleSubmit);
  await refreshTable();
});
