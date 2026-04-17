const shell = document.querySelector(".editor-shell");

if (shell) {
  const documentId = shell.dataset.documentId;
  const editor = document.getElementById("rich-editor");
  const titleInput = document.getElementById("document-title");
  const saveButton = document.getElementById("save-button");
  const saveStatus = document.getElementById("save-status");
  const wordCount = document.getElementById("word-count");
  const blockStyle = document.getElementById("block-style");
  const toolbarButtons = Array.from(document.querySelectorAll(".toolbar button[data-command]"));

  let saveTimer = null;
  let dirty = false;

  const setStatus = (message, tone = "neutral") => {
    saveStatus.textContent = message;
    saveStatus.dataset.tone = tone;
  };

  const updateWordCount = () => {
    const text = editor.innerText.replace(/\s+/g, " ").trim();
    const words = text ? text.split(" ").length : 0;
    wordCount.textContent = `${words} word${words === 1 ? "" : "s"}`;
  };

  const markDirty = () => {
    dirty = true;
    setStatus("Unsaved changes", "warn");
  };

  const queueAutosave = () => {
    clearTimeout(saveTimer);
    saveTimer = window.setTimeout(() => {
      void saveDocument();
    }, 1600);
  };

  const saveDocument = async () => {
    const payload = {
      title: titleInput.value.trim(),
      content_html: editor.innerHTML.trim(),
    };

    if (!payload.title) {
      setStatus("Title is required before saving.", "error");
      return;
    }

    saveButton.disabled = true;
    setStatus("Saving...", "neutral");

    try {
      const response = await fetch(`/api/documents/${documentId}/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to save document.");
      }

      dirty = false;
      const formatted = new Date(data.updated_at).toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
      });
      setStatus(`Saved ${formatted}`, "success");
    } catch (error) {
      setStatus(error.message || "Unable to save document.", "error");
    } finally {
      saveButton.disabled = false;
    }
  };

  const applyCommand = (command, value = null) => {
    editor.focus();
    document.execCommand(command, false, value);
    markDirty();
    updateWordCount();
    queueAutosave();
  };

  toolbarButtons.forEach((button) => {
    button.addEventListener("click", () => {
      applyCommand(button.dataset.command);
    });
  });

  blockStyle.addEventListener("change", (event) => {
    const tagName = `<${event.target.value.toLowerCase()}>`;
    applyCommand("formatBlock", tagName);
  });

  saveButton.addEventListener("click", () => {
    void saveDocument();
  });

  titleInput.addEventListener("input", () => {
    markDirty();
    queueAutosave();
  });

  editor.addEventListener("input", () => {
    markDirty();
    updateWordCount();
    queueAutosave();
  });

  editor.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      void saveDocument();
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (!dirty) {
      return;
    }
    event.preventDefault();
    event.returnValue = "";
  });

  updateWordCount();
}
