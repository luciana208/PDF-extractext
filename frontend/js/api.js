const API_URL = "http://127.0.0.1:8000/api/v1/documents/";

export async function getDocuments() {
  const res = await fetch(API_URL);
  return await res.json();
}

export async function getDocument(id) {
  const res = await fetch(`${API_URL}${id}`);
  return await res.json();
}

export async function uploadDocument(file, customName) {
  const formData = new FormData();
  formData.append("file", file);

  if (customName) {
    formData.append("custom_name", customName);
  }

  const res = await fetch(API_URL, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Error subiendo archivo");
  }

  return await res.json();
}

export async function deleteDocument(id) {
  const res = await fetch(`${API_URL}${id}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Error eliminando documento");
  }

  return await res.json();
}