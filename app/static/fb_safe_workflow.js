(function () {
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  async function fetchJSON(url, options) {
    const token = csrfToken();
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-CSRFToken": token } : {}),
        ...(options && options.headers ? options.headers : {}),
      },
      ...options,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }
    return data;
  }

  function linesToArray(value) {
    return value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function renderStatusBadge(status) {
    return `<span class="status-badge status-${status}">${status.replaceAll("_", " ")}</span>`;
  }

  function renderMiniChips(chips) {
    if (!chips || !chips.length) {
      return "";
    }
    return `<div class="chip-row">${chips
      .map((chip) => `<span class="mini-chip warn">${escapeHtml(chip)}</span>`)
      .join("")}</div>`;
  }

  function humanizeTimestamp(value) {
    if (!value) return "never";
    const ts = new Date(value);
    if (Number.isNaN(ts.getTime())) return value;
    const deltaSeconds = Math.max(0, Math.floor((Date.now() - ts.getTime()) / 1000));
    if (deltaSeconds < 60) return "just now";
    if (deltaSeconds < 3600) return `${Math.floor(deltaSeconds / 60)}m ago`;
    if (deltaSeconds < 86400) return `${Math.floor(deltaSeconds / 3600)}h ago`;
    if (deltaSeconds < 604800) return `${Math.floor(deltaSeconds / 86400)}d ago`;
    return ts.toLocaleDateString();
  }

  function buildGroupWarnings(group, extraContext) {
    const chips = Array.isArray(group.warning_chips) ? [...group.warning_chips] : [];
    const context = extraContext || {};
    if (context.existingRunGroupIds && context.existingRunGroupIds.has(group.id)) {
      chips.push("already in unfinished run");
    }
    return Array.from(new Set(chips));
  }

  async function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }

  function initPostGenerator(page) {
    const state = {
      selectedId: window.fbWorkflowInitialSelectedVariant ? window.fbWorkflowInitialSelectedVariant.id : null,
      variants: Array.isArray(window.fbWorkflowInitialVariants) ? window.fbWorkflowInitialVariants : [],
    };

    const elements = {
      tone: document.getElementById("tone"),
      lengthMode: document.getElementById("length_mode"),
      ctaMode: document.getElementById("cta_mode"),
      ctaValue: document.getElementById("cta_value"),
      salaryHint: document.getElementById("salary_hint"),
      employmentType: document.getElementById("employment_type"),
      requirements: document.getElementById("requirements"),
      benefits: document.getElementById("benefits"),
      allowCompanyName: document.getElementById("allow_company_name"),
      generateButton: document.getElementById("generate-variant-btn"),
      status: document.getElementById("generator-status"),
      variantList: document.getElementById("variant-list"),
      variantCount: document.getElementById("variant-count-badge"),
      editorHeadline: document.getElementById("editor-headline"),
      editorText: document.getElementById("editor-full-text"),
      editorCta: document.getElementById("editor-cta"),
      editorMeta: document.getElementById("editor-variant-meta"),
      editorChars: document.getElementById("editor-char-count"),
      preview: document.getElementById("variant-preview"),
      approveButton: document.getElementById("approve-variant-btn"),
      copyButton: document.getElementById("copy-variant-btn"),
      continueButton: document.getElementById("continue-variant-btn"),
    };

    function selectedVariant() {
      return state.variants.find((variant) => variant.id === state.selectedId) || null;
    }

    function syncEditor() {
      const variant = selectedVariant();
      if (!variant) {
        elements.editorHeadline.value = "";
        elements.editorText.value = "";
        elements.editorCta.value = "";
        elements.preview.textContent = "Preview will appear here.";
        setText("editor-variant-meta", "No selection");
        setText("editor-char-count", "0 chars");
        elements.continueButton.style.display = "none";
        return;
      }
      elements.editorHeadline.value = variant.headline || "";
      elements.editorText.value = variant.full_text || "";
      elements.editorCta.value = variant.cta_text || "";
      elements.preview.textContent = variant.full_text || "";
      setText("editor-variant-meta", `${variant.tone} / ${variant.length_mode} / ${variant.status}`);
      setText("editor-char-count", `${(variant.full_text || "").length} chars`);
      elements.continueButton.style.display = variant.status === "approved" ? "inline-flex" : "none";
      elements.approveButton.textContent = variant.status === "approved" ? "Re-save & Select Groups" : "Approve & Select Groups";
    }

    function renderVariantList() {
      setText("variant-count-badge", `${state.variants.length} drafts`);
      if (!state.variants.length) {
        elements.variantList.className = "variant-list empty-state";
        elements.variantList.textContent = "Generate a first draft to start the flow.";
        return;
      }

      elements.variantList.className = "variant-list";
      elements.variantList.innerHTML = state.variants
        .map((variant) => {
          const activeClass = variant.id === state.selectedId ? " active" : "";
          return `
            <button type="button" class="variant-card${activeClass}" data-variant-id="${variant.id}">
              <div class="row">
                <strong>${escapeHtml(variant.headline || variant.variant_label)}</strong>
                ${renderStatusBadge(variant.status)}
              </div>
              <div class="small muted">${escapeHtml(variant.tone)} • ${escapeHtml(variant.length_mode)} • ${variant.char_count || 0} chars</div>
              <div class="variant-snippet">${escapeHtml((variant.full_text || "").slice(0, 180))}</div>
            </button>
          `;
        })
        .join("");

      elements.variantList.querySelectorAll("[data-variant-id]").forEach((button) => {
        button.addEventListener("click", () => {
          state.selectedId = Number(button.dataset.variantId);
          renderVariantList();
          syncEditor();
        });
      });
    }

    async function generateVariant() {
      elements.generateButton.disabled = true;
      elements.status.textContent = "Generating and saving draft...";
      try {
        const payload = {
          vacancy_id: Number(page.dataset.vacancyId),
          tone: elements.tone.value,
          length_mode: elements.lengthMode.value,
          cta_mode: elements.ctaMode.value,
          cta_value: elements.ctaValue.value.trim() || null,
          salary_hint: elements.salaryHint.value.trim() || null,
          employment_type: elements.employmentType.value.trim() || null,
          requirements: linesToArray(elements.requirements.value),
          benefits: linesToArray(elements.benefits.value),
          allow_company_name: elements.allowCompanyName.checked,
          save: true,
          save_status: "draft",
        };
        const data = await fetchJSON("/api/fb/post-variants/generate", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        const variant = data.saved_variant;
        state.variants.unshift(variant);
        state.selectedId = variant.id;
        renderVariantList();
        syncEditor();
        elements.status.textContent = `Draft ${variant.id} ready. Edit and approve when ready.`;
      } catch (error) {
        elements.status.textContent = error.message;
      } finally {
        elements.generateButton.disabled = false;
      }
    }

    async function approveVariant() {
      const variant = selectedVariant();
      if (!variant) {
        elements.status.textContent = "Generate a draft before approving.";
        return;
      }
      elements.approveButton.disabled = true;
      elements.status.textContent = "Saving approved variant...";
      try {
        const data = await fetchJSON(`/api/fb/post-variants/${variant.id}/approve`, {
          method: "POST",
          body: JSON.stringify({
            headline: elements.editorHeadline.value.trim(),
            full_text: elements.editorText.value,
            cta_text: elements.editorCta.value.trim(),
          }),
        });
        const index = state.variants.findIndex((item) => item.id === data.id);
        if (index >= 0) {
          state.variants[index] = data;
        }
        state.selectedId = data.id;
        renderVariantList();
        syncEditor();
        window.location.href = `${page.dataset.groupSelectorUrl}?variant_id=${data.id}`;
      } catch (error) {
        elements.status.textContent = error.message;
      } finally {
        elements.approveButton.disabled = false;
      }
    }

    elements.generateButton.addEventListener("click", generateVariant);
    elements.approveButton.addEventListener("click", approveVariant);
    elements.copyButton.addEventListener("click", async () => {
      const text = elements.editorText.value;
      if (!text) {
        elements.status.textContent = "Nothing to copy yet.";
        return;
      }
      await copyText(text);
      elements.status.textContent = "Copied selected variant text.";
    });
    elements.continueButton.addEventListener("click", () => {
      const variant = selectedVariant();
      if (!variant) {
        elements.status.textContent = "No saved variant selected.";
        return;
      }
      window.location.href = `${page.dataset.groupSelectorUrl}?variant_id=${variant.id}`;
    });
    elements.editorText.addEventListener("input", () => {
      elements.preview.textContent = elements.editorText.value;
      setText("editor-char-count", `${elements.editorText.value.length} chars`);
    });

    if (!state.selectedId && state.variants.length) {
      state.selectedId = state.variants[0].id;
    }
    syncEditor();
    renderVariantList();
  }

  function initGroupSelector(page) {
    const state = {
      groups: [],
      selectedIds: new Set(),
      variant: window.fbWorkflowInitialVariant || null,
      existingRunGroupIds: new Set(Array.isArray(window.fbWorkflowExistingRunGroupIds) ? window.fbWorkflowExistingRunGroupIds : []),
    };

    const elements = {
      search: document.getElementById("group-search"),
      category: document.getElementById("group-category"),
      city: document.getElementById("group-city"),
      minActivity: document.getElementById("group-min-activity"),
      isActive: document.getElementById("group-is-active"),
      loadButton: document.getElementById("load-groups-btn"),
      loadStatus: document.getElementById("group-load-status"),
      tableBody: document.getElementById("groups-table-body"),
      selectedCount: document.getElementById("selected-groups-count"),
      runPreview: document.getElementById("group-run-preview"),
      runName: document.getElementById("posting-run-name"),
      runNotes: document.getElementById("posting-run-notes"),
      createRunButton: document.getElementById("create-posting-run-btn"),
      createRunStatus: document.getElementById("create-run-status"),
    };

    function updateSelectionUI() {
      const count = state.selectedIds.size;
      setText("selected-groups-count", `${count} selected`);
      setText("group-run-preview", count ? `${count} groups ready` : "Choose groups first");
      elements.createRunButton.disabled = !count || !state.variant;
    }

    function renderGroups() {
      if (!state.groups.length) {
        elements.tableBody.innerHTML = '<tr><td colspan="7" class="muted">No groups match the current filters.</td></tr>';
        return;
      }
      elements.tableBody.innerHTML = state.groups
        .map((group) => {
          const checked = state.selectedIds.has(group.id) ? "checked" : "";
          return `
            <tr>
              <td><input type="checkbox" data-group-id="${group.id}" ${checked}></td>
              <td>
                <div><strong>${escapeHtml(group.name)}</strong></div>
                <div class="small muted">${escapeHtml(group.facebook_slug || "")}</div>
                ${renderMiniChips(buildGroupWarnings(group, { existingRunGroupIds: state.existingRunGroupIds }))}
              </td>
              <td>${escapeHtml(group.primary_category || "-")}</td>
              <td>${escapeHtml(group.city || group.region || "-")}</td>
              <td>${escapeHtml(group.language_code || "-")}</td>
              <td>${group.activity_rating || "-"}</td>
              <td>${escapeHtml(group.last_posted_label || humanizeTimestamp(group.last_posted_at))}</td>
            </tr>
          `;
        })
        .join("");

      elements.tableBody.querySelectorAll("[data-group-id]").forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
          const groupId = Number(checkbox.dataset.groupId);
          if (checkbox.checked) {
            state.selectedIds.add(groupId);
          } else {
            state.selectedIds.delete(groupId);
          }
          updateSelectionUI();
        });
      });
    }

    async function loadGroups() {
      elements.loadButton.disabled = true;
      elements.loadStatus.textContent = "Loading groups...";
      try {
        const params = new URLSearchParams();
        if (elements.search.value.trim()) params.set("search", elements.search.value.trim());
        if (elements.category.value) params.set("primary_category", elements.category.value);
        if (elements.city.value.trim()) params.set("city", elements.city.value.trim());
        if (elements.minActivity.value) params.set("min_activity", elements.minActivity.value);
        params.set("is_active", String(elements.isActive.checked));

        const data = await fetchJSON(`/api/fb/groups?${params.toString()}`);
        state.groups = data.groups || [];
        renderGroups();
        elements.loadStatus.textContent = `${data.count} groups loaded.`;
      } catch (error) {
        elements.loadStatus.textContent = error.message;
      } finally {
        elements.loadButton.disabled = false;
      }
    }

    async function createRun() {
      if (!state.variant) {
        elements.createRunStatus.textContent = "Approve a variant before creating a run.";
        return;
      }
      if (!state.selectedIds.size) {
        elements.createRunStatus.textContent = "Select at least one group.";
        return;
      }
      elements.createRunButton.disabled = true;
      elements.createRunStatus.textContent = "Creating posting run...";
      try {
        const data = await fetchJSON("/api/fb/posting-runs", {
          method: "POST",
          body: JSON.stringify({
            vacancy_id: Number(page.dataset.vacancyId),
            post_variant_id: Number(state.variant.id),
            group_ids: Array.from(state.selectedIds),
            name: elements.runName.value.trim(),
            notes: elements.runNotes.value.trim(),
          }),
        });
        window.location.href = `/facebook/posting-runs/${data.id}/queue`;
      } catch (error) {
        elements.createRunStatus.textContent = error.message;
      } finally {
        elements.createRunButton.disabled = false;
      }
    }

    elements.loadButton.addEventListener("click", loadGroups);
    elements.createRunButton.addEventListener("click", createRun);
    updateSelectionUI();
    loadGroups();
  }

  function initPostingQueue(page) {
    const state = {
      run: null,
      selectedItemId: null,
    };

    const elements = {
      progressBadge: document.getElementById("queue-progress-badge"),
      postPreview: document.getElementById("queue-post-preview"),
      currentStatus: document.getElementById("queue-current-status"),
      currentGroup: document.getElementById("queue-current-group"),
      actionStatus: document.getElementById("queue-action-status"),
      queueTableBody: document.getElementById("queue-items-table-body"),
      runName: document.getElementById("queue-run-name"),
      runContext: document.getElementById("queue-run-context"),
      runSignals: document.getElementById("queue-run-signals"),
      postUrl: document.getElementById("queue-post-url"),
      groupNote: document.getElementById("queue-group-note"),
      skipReason: document.getElementById("queue-skip-reason"),
      openGroup: document.getElementById("queue-open-group-btn"),
      markPosted: document.getElementById("queue-mark-posted-btn"),
      skipButton: document.getElementById("queue-skip-btn"),
      copyPost: document.getElementById("queue-copy-post-btn"),
      resultStatus: document.getElementById("result-status"),
      responseCount: document.getElementById("response-count"),
      cvCount: document.getElementById("cv-count"),
      interviewCount: document.getElementById("interview-count"),
      hireCount: document.getElementById("hire-count"),
      resultNote: document.getElementById("result-note"),
      resultSave: document.getElementById("save-result-btn"),
      resultSaveStatus: document.getElementById("result-save-status"),
      resultStatusBadge: document.getElementById("queue-result-status-badge"),
    };

    function selectedItem() {
      if (!state.run) return null;
      return state.run.queue_items.find((item) => item.id === state.selectedItemId) || null;
    }

    function pickDefaultItem(run) {
      return (
        run.queue_items.find((item) => item.status === "current") ||
        run.queue_items.find((item) => item.status === "opened") ||
        run.queue_items.find((item) => item.status === "pending") ||
        run.queue_items[0] ||
        null
      );
    }

    function hydrateSelectedItem(item) {
      if (!item) {
        elements.currentGroup.innerHTML = '<div class="muted">No queue item selected.</div>';
        elements.currentStatus.textContent = "No item";
        return;
      }
      elements.currentStatus.textContent = item.status;
      elements.currentGroup.innerHTML = `
        <div><span class="muted">Group</span><strong>${escapeHtml(item.group.name)}</strong></div>
        <div><span class="muted">Location</span><strong>${escapeHtml(item.group.city || item.group.region || "-")}</strong></div>
        <div><span class="muted">Rules</span><strong>${escapeHtml(item.group.posting_rules_summary || "-")}</strong></div>
        <div><span class="muted">Last posted</span><strong>${escapeHtml(item.group.last_posted_label || humanizeTimestamp(item.group.last_posted_at))}</strong></div>
        <div><span class="muted">Facebook</span><a href="${item.group.facebook_url}" target="_blank" rel="noopener">Open direct link</a></div>
        ${renderMiniChips(buildGroupWarnings(item.group))}
      `;
      elements.postUrl.value = item.post_url_manual || "";
      elements.groupNote.value = item.group_note || "";
      elements.skipReason.value = item.skip_reason || "";
      const result = item.result || {};
      elements.resultStatus.value = result.result_status || "posted";
      elements.responseCount.value = result.response_count ?? "";
      elements.cvCount.value = result.cv_count ?? "";
      elements.interviewCount.value = result.interview_count ?? "";
      elements.hireCount.value = result.hire_count ?? "";
      elements.resultNote.value = result.result_note || "";
      elements.resultStatusBadge.textContent = result.result_status || "Optional";
    }

    function renderQueue(run) {
      state.run = run;
      const currentSelection = run.queue_items.find((item) => item.id === state.selectedItemId) || null;
      if (
        !currentSelection ||
        ["posted", "skipped", "failed"].includes(currentSelection.status)
      ) {
        const defaultItem = pickDefaultItem(run);
        state.selectedItemId = defaultItem ? defaultItem.id : null;
      }

      const postedCount = run.queue_items.filter((item) => item.status === "posted").length;
      setText("queue-progress-badge", `${postedCount}/${run.queue_items.length} posted`);
      setText("queue-run-name", run.name || `Run #${run.id}`);
      setText(
        "queue-run-context",
        `${run.status_label || run.status} · ${run.attention_label || ""} · last activity ${run.last_action_at_label || humanizeTimestamp(run.last_action_at)}`
      );
      elements.runSignals.innerHTML = `
        <span class="mini-chip ${run.attention_label === "Needs attention" ? "warn" : "ok"}">${escapeHtml(run.attention_label || "")}</span>
        ${run.latest_signal ? `<span class="mini-chip ok">Latest signal: ${escapeHtml(run.latest_signal.label || run.latest_signal.status)}</span>` : ""}
        ${run.latest_signal && run.latest_signal.updated_label ? `<span class="mini-chip">${escapeHtml(run.latest_signal.updated_label)}</span>` : ""}
      `;
      elements.postPreview.textContent = run.post_variant.full_text || "";

      elements.queueTableBody.innerHTML = run.queue_items
        .map((item) => {
          const activeClass = item.id === state.selectedItemId ? " queue-row-active" : "";
          return `
            <tr class="${activeClass}" data-queue-item-id="${item.id}">
              <td>${item.position}</td>
              <td>
                <div><strong>${escapeHtml(item.group.name)}</strong></div>
                ${renderMiniChips(buildGroupWarnings(item.group))}
              </td>
              <td>${renderStatusBadge(item.status)}</td>
              <td>${escapeHtml(item.group.city || item.group.region || "-")}</td>
              <td>${item.group.activity_rating || "-"}</td>
              <td>${escapeHtml((item.result && (item.result.result_status_label || item.result.result_status)) || "-")}</td>
            </tr>
          `;
        })
        .join("");

      elements.queueTableBody.querySelectorAll("[data-queue-item-id]").forEach((row) => {
        row.addEventListener("click", () => {
          state.selectedItemId = Number(row.dataset.queueItemId);
          renderQueue(state.run);
        });
      });

      hydrateSelectedItem(selectedItem());
    }

    async function refreshRun() {
      const run = await fetchJSON(`/api/fb/posting-runs/${page.dataset.runId}`);
      renderQueue(run);
    }

    async function updateQueue(action, payload) {
      const item = selectedItem();
      if (!item) {
        elements.actionStatus.textContent = "No queue item selected.";
        return null;
      }
      elements.actionStatus.textContent = `Saving ${action}...`;
      const data = await fetchJSON(`/api/fb/queue-items/${item.id}/action`, {
        method: "POST",
        body: JSON.stringify({ action, ...payload }),
      });
      renderQueue(data);
      elements.actionStatus.textContent = `Queue item updated: ${action}.`;
      return selectedItem();
    }

    elements.copyPost.addEventListener("click", async () => {
      if (!state.run) return;
      await copyText(state.run.post_variant.full_text || "");
      await updateQueue("copied", {});
    });

    elements.openGroup.addEventListener("click", async () => {
      const item = selectedItem();
      if (!item) return;
      await updateQueue("opened", {});
      window.open(item.group.facebook_url, "_blank", "noopener");
    });

    elements.markPosted.addEventListener("click", async () => {
      const item = selectedItem();
      if (!item) return;
      try {
        const data = await fetchJSON(`/api/fb/queue-items/${item.id}/mark-posted`, {
          method: "POST",
          body: JSON.stringify({
            post_url_manual: elements.postUrl.value.trim(),
            group_note: elements.groupNote.value.trim(),
          }),
        });
        renderQueue(data);
        elements.actionStatus.textContent = "Marked as posted.";
      } catch (error) {
        elements.actionStatus.textContent = error.message;
      }
    });

    elements.skipButton.addEventListener("click", async () => {
      const item = selectedItem();
      if (!item) return;
      try {
        const data = await fetchJSON(`/api/fb/queue-items/${item.id}/skip`, {
          method: "POST",
          body: JSON.stringify({
            skip_reason: elements.skipReason.value.trim(),
            group_note: elements.groupNote.value.trim(),
          }),
        });
        renderQueue(data);
        elements.actionStatus.textContent = "Item skipped.";
      } catch (error) {
        elements.actionStatus.textContent = error.message;
      }
    });

    elements.resultSave.addEventListener("click", async () => {
      const item = selectedItem();
      if (!item) {
        elements.resultSaveStatus.textContent = "No queue item selected.";
        return;
      }
      elements.resultSaveStatus.textContent = "Saving result snapshot...";
      try {
        const result = await fetchJSON(`/api/fb/results/${item.id}`, {
          method: "POST",
          body: JSON.stringify({
            result_status: elements.resultStatus.value,
            response_count: elements.responseCount.value || null,
            cv_count: elements.cvCount.value || null,
            interview_count: elements.interviewCount.value || null,
            hire_count: elements.hireCount.value || null,
            result_note: elements.resultNote.value.trim(),
          }),
        });
        elements.resultSaveStatus.textContent = `Saved result: ${result.result_status}.`;
        await refreshRun();
      } catch (error) {
        elements.resultSaveStatus.textContent = error.message;
      }
    });

    refreshRun().catch((error) => {
      elements.actionStatus.textContent = error.message;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector("[data-page]");
    if (!page) return;
    if (page.dataset.page === "post-generator") initPostGenerator(page);
    if (page.dataset.page === "group-selector") initGroupSelector(page);
    if (page.dataset.page === "posting-queue") initPostingQueue(page);
  });
})();
