let skus = [], activeStockId = null, activeAction = null;
let skuBusy = false, catalogReady = false;
let branches = [], selectedBranchId = null;
let lowStockThreshold = 5;
const skuElement = id => document.getElementById(id);
skuElement('refreshInventory').addEventListener('click', refreshInventory);
skuElement('branchSelect').addEventListener('change', async event => {
    selectedBranchId = event.target.value;
    renderSkus();
});
skuElement('inventorySearch').addEventListener('input', renderSkus);
skuElement('inventoryStockFilter').addEventListener('change', renderSkus);
function skuName(v) {
    if (v.display_name) return v.display_name;
    const name = v.variant_name || '';
    const product = v.product_name || '';
    const optionName = product && name.startsWith(`${product} / `) ? name.slice(product.length + 3) : name;
    if (product && (!optionName || optionName === product || optionName === 'Default variant' || optionName === 'Variant' || optionName.startsWith('SKU '))) return product;
    if (product && optionName) return `${product} / ${optionName}`;
    if (optionName) return optionName;
    return `SKU ${String(v.id).slice(0, 8)}`;
}
const actionIcons = {
    increase: '<path d="M12 5v14M5 12h14"/>',
    decrease: '<path d="M5 12h14"/>',
    set: '<path d="M4 7h16M7 12h10M10 17h4"/>',
    transfer: '<path d="M17 3l4 4-4 4M21 7H9M7 21l-4-4 4-4M3 17h12"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5M12 7v5l3 2"/>'
};
function actionButton(action, index, label) {
    return `<button type="button" data-action="${action}" data-index="${index}" aria-label="${label}" title="${label}" class="sku-action"><svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${actionIcons[action]}</svg><span>${label}</span></button>`;
}
function updateBusyState() {
    skuElement('inventoryWorkspace').disabled = skuBusy || !catalogReady;
    skuElement('inventoryWorkspace').setAttribute('aria-busy', String(skuBusy));
}
async function loadBranches() {
    branches = await apiFetch('/branches/');
    const sel = skuElement('branchSelect');
    sel.innerHTML = branches.map(b => `<option value="${b.id}">${esc(b.name)} (${esc(b.branch_code)})</option>`).join('');
    if (!selectedBranchId || !branches.some(b => b.id === selectedBranchId)) {
        selectedBranchId = branches[0]?.id || null;
    }
    sel.value = selectedBranchId || '';
}
async function loadSkus() {
    // Stock is now branch-scoped (VariantBranchStock ledger+cache) — every
    // tracked variant carries a stock_by_branch map, never a single global
    // stock_quantity column.
    const [variants, business] = await Promise.all([
        apiFetch('/variants?tracked_only=true'),
        apiFetch('/business/'),
    ]);
    if (!Array.isArray(variants)) throw new Error('Unexpected inventory response');
    lowStockThreshold = Number.isSafeInteger(business.low_stock_threshold)
        ? business.low_stock_threshold : 5;
    skus = variants.filter(variant => variant.tracks_inventory === true);
    catalogReady = true;
    renderSkus();
}
function branchStock(v) {
    if (!selectedBranchId) return 0;
    return (v.stock_by_branch && v.stock_by_branch[selectedBranchId]) || 0;
}
// Every /variants row already carries stock for every branch
// (stock_by_branch is never filtered server-side to just one branch) —
// this sums it so "overall" stock is visible alongside the per-branch
// figure, instead of discarding everything but the selected branch.
function overallStock(v) {
    if (!v.stock_by_branch) return 0;
    return Object.values(v.stock_by_branch).reduce((sum, n) => sum + (n || 0), 0);
}
function perBranchBreakdown(v) {
    if (!v.stock_by_branch) return '';
    return branches
        .map(b => `${b.name}: ${v.stock_by_branch[b.id] || 0}`)
        .join('\n');
}
function renderSkus() {
    const branchLabel = branches.find(b => b.id === selectedBranchId)?.name || '—';
    const rows = filteredSkus();
    skuElement('inventoryStatus').textContent = `${rows.length} of ${skus.length} tracked variants shown, stock at ${branchLabel}.`;
    skuElement('skuEmpty').classList.toggle('hidden', rows.length > 0);
    skuElement('skuEmpty').textContent = skus.length ? 'No inventory matches the current search and stock filter.' : 'No tracked variants.';
    skuElement('skuRows').innerHTML = rows.map(({ v, index }) => {
        const unsellableBadge = v.sellable === false
            ? `<span class="block mt-1 inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5" title="${esc(v.sellable_reason || '')}">
                 <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 9v4M12 17h.01M10.29 3.86l-8.18 14.18A2 2 0 004 21h16a2 2 0 001.89-2.96L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                 Can't be sold yet
               </span>`
            : '';
        const isLow = branchStock(v) <= lowStockThreshold;
        const lowBadge = isLow ? `<span class="block mt-1 text-xs font-medium text-amber-700">Low stock (threshold ${esc(lowStockThreshold)})</span>` : '';
        return `<tr class="sku-row border-t align-top ${isLow ? 'bg-amber-50/50' : ''}">
        <td class="p-3" data-label="Variant"><span class="font-medium">${esc(skuName(v))}</span><span class="block text-xs text-slate-500">ID ${esc(String(v.id).slice(0, 8))}</span>${unsellableBadge}</td>
        <td class="p-3 font-semibold" data-label="Stock">${esc(branchStock(v))}${lowBadge}</td>
        <td class="p-3" data-label="Overall stock"><span class="font-semibold" title="${esc(perBranchBreakdown(v))}">${esc(overallStock(v))}</span><span class="block text-xs text-slate-400">all branches</span></td>
        <td class="p-3" data-label="Actions"><div class="sku-actions">${actionButton('increase', index, 'Increase')}${actionButton('decrease', index, 'Decrease')}${actionButton('set', index, 'Set stock')}${branches.length > 1 ? actionButton('transfer', index, 'Transfer') : ''}${actionButton('history', index, 'History')}</div></td>
    </tr>`;
    }).join('');
}
function filteredSkus() {
    const query = skuElement('inventorySearch').value.trim().toLocaleLowerCase();
    const stockFilter = skuElement('inventoryStockFilter').value;
    return skus.map((v, index) => ({ v, index })).filter(({ v }) => {
        const searchable = [skuName(v), v.product_name, v.variant_name, v.display_name, v.id]
            .filter(Boolean).join(' ').toLocaleLowerCase();
        if (query && !searchable.includes(query)) return false;
        const quantity = branchStock(v);
        if (stockFilter === 'in_stock' && quantity <= 0) return false;
        if (stockFilter === 'out_of_stock' && quantity !== 0) return false;
        if (stockFilter === 'low_stock' && quantity > lowStockThreshold) return false;
        return true;
    });
}
async function skuAction(work, errorId = 'inventoryError') {
    if (skuBusy) return false;
    skuBusy = true; updateBusyState(); skuElement(errorId).textContent = '';
    try { await work(); return true; }
    catch (e) { skuElement(errorId).textContent = e.message; return false; }
    finally { skuBusy = false; updateBusyState(); }
}
async function refreshInventory() {
    if (skuBusy) return;
    skuBusy = true; updateBusyState(); skuElement('refreshInventory').disabled = true; skuElement('inventoryStatus').textContent = 'Loading inventory...'; skuElement('inventoryError').textContent = '';
    try { await loadBranches(); await loadSkus(); }
    catch (e) {
        catalogReady = false; skus = [];
        skuElement('inventoryError').textContent = `Inventory could not be loaded: ${e.message}.`;
        skuElement('inventoryStatus').textContent = 'Inventory unavailable.';
        skuElement('skuRows').replaceChildren(); skuElement('skuEmpty').textContent = 'Inventory unavailable until refresh succeeds.'; skuElement('skuEmpty').classList.remove('hidden');
    }
    finally { skuBusy = false; updateBusyState(); skuElement('refreshInventory').disabled = false; }
}
function openStockAction(v, action) {
    activeStockId = v.id; activeAction = action;
    skuElement('stockVariantName').textContent = skuName(v);
    skuElement('stockActionTitle').textContent = action === 'set' ? 'Set stock' : `${action[0].toUpperCase()}${action.slice(1)} stock`;
    skuElement('stockQuantity').value = action === 'set' ? branchStock(v) : '';
    skuElement('stockError').textContent = '';
    // A variant can go stale (a required Variant Option Group attached, or
    // made required, after this SKU already existed) without being deleted —
    // stock can still be recorded against it, but it will never actually be
    // sellable until fixed. Say so plainly before the admin adds stock to it,
    // instead of letting them discover this later at checkout.
    const warn = skuElement('stockUnsellableWarning');
    if (v.sellable === false) {
        warn.textContent = v.sellable_reason || "This SKU isn't sellable right now — adding stock won't change that.";
        warn.classList.remove('hidden');
    } else {
        warn.classList.add('hidden');
    }
    skuElement('stockDialog').showModal();
}
function openTransferAction(v) {
    activeStockId = v.id;
    const fromBranch = branches.find(b => b.id === selectedBranchId);
    skuElement('transferVariantName').textContent = skuName(v);
    skuElement('transferFromLabel').textContent = `From ${fromBranch ? fromBranch.name : 'the selected branch'} — ${branchStock(v)} in stock.`;
    const toSelect = skuElement('transferToBranch');
    toSelect.innerHTML = branches.filter(b => b.id !== selectedBranchId)
        .map(b => `<option value="${b.id}">${esc(b.name)} (${esc(b.branch_code)})</option>`).join('');
    skuElement('transferQuantity').value = '';
    skuElement('transferNote').value = '';
    skuElement('transferError').textContent = '';
    skuElement('transferDialog').showModal();
}

skuElement('skuRows').addEventListener('click', async event => {
    const button = event.target.closest('button'); if (!button || skuBusy) return;
    const item = skus[Number(button.dataset.index)]; if (!item) return;
    if (button.dataset.action === 'history') {
        skuElement('skuHistory').textContent = 'Loading...'; skuElement('historyDialog').showModal();
        try { const rows = await apiFetch(`/variants/${item.id}/history?branch_id=${selectedBranchId}`); skuElement('skuHistory').innerHTML = rows.map(r => `<p class="border-b py-2">${esc(new Date(r.created_at).toLocaleString())}: ${esc(r.adjustment_type)} ${esc(r.quantity_change)}, balance ${esc(r.resulting_quantity)}${r.note ? ` — ${esc(r.note)}` : ''}</p>`).join('') || 'No stock adjustments yet at this branch.'; }
        catch (e) { skuElement('skuHistory').textContent = e.message; }
        return;
    }
    if (button.dataset.action === 'transfer') { openTransferAction(item); return; }
    openStockAction(item, button.dataset.action);
});
skuElement('transferForm').addEventListener('submit', async event => {
    event.preventDefault();
    if (!selectedBranchId) { skuElement('transferError').textContent = 'No branch selected.'; return; }
    const toBranchId = skuElement('transferToBranch').value;
    if (!toBranchId) { skuElement('transferError').textContent = 'Choose a destination branch.'; return; }
    const quantity = Number(skuElement('transferQuantity').value);
    if (!Number.isSafeInteger(quantity) || quantity < 1) { skuElement('transferError').textContent = 'Enter a valid whole quantity.'; return; }
    const note = skuElement('transferNote').value.trim() || undefined;
    const ok = await skuAction(async () => {
        const updated = await apiFetch(`/variants/${activeStockId}/transfer`, {
            method: 'POST',
            body: JSON.stringify({ from_branch_id: selectedBranchId, to_branch_id: toBranchId, quantity, note })
        });
        const index = skus.findIndex(v => v.id === activeStockId);
        // See the identical note in the stockForm handler below — this
        // merge trusts `updated` to be complete; extend
        // api/v1/variants.py::_to_response() if a new field is ever added,
        // not this spread.
        if (index >= 0) skus[index] = { ...skus[index], ...updated };
        skuElement('transferDialog').close();
        const stillVisible = index >= 0 && filteredSkus().some(({ v }) => v.id === activeStockId);
        renderSkus();
        if (index >= 0 && !stillVisible) {
            const filterLabel = skuElement('inventoryStockFilter').selectedOptions[0]?.text || 'the current filter';
            showToast(`Stock transferred. This item no longer matches "${filterLabel}", so it's hidden — not deleted.`);
        }
    }, 'transferError');
    if (!ok) skuElement('transferDialog').showModal();
});
skuElement('stockForm').addEventListener('submit', async event => {
    event.preventDefault();
    if (!selectedBranchId) { skuElement('stockError').textContent = 'No branch selected.'; return; }
    const quantity = Number(skuElement('stockQuantity').value);
    if (!Number.isSafeInteger(quantity) || quantity < (activeAction === 'set' ? 0 : 1)) { skuElement('stockError').textContent = 'Enter a valid whole quantity.'; return; }
    const path = activeAction === 'set'
        ? `/variants/${activeStockId}/stock?branch_id=${selectedBranchId}`
        : `/variants/${activeStockId}/stock/${activeAction}?branch_id=${selectedBranchId}`;
    const body = activeAction === 'set' ? { stock_quantity: quantity } : { quantity };
    const ok = await skuAction(async () => {
        const updated = await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
        const index = skus.findIndex(v => v.id === activeStockId);
        // This spread trusts `updated` to be a COMPLETE row, including
        // product_name/variant_name — those used to come back null from
        // this endpoint (only the list endpoint computed them), which this
        // exact merge then used to overwrite the correct cached name with
        // null (see api/v1/variants.py::_to_response, fixed to always
        // compute them). If a future field is ever added to VariantResponse
        // and populated only by the list endpoint, this merge will silently
        // blank it out here again — extend _to_response(), not this file.
        if (index >= 0) skus[index] = { ...skus[index], ...updated };
        skuElement('stockDialog').close();
        // The row isn't deleted or lost — it just no longer matches the
        // active "Stock filter" (e.g. it left "Out of stock" once restocked,
        // or left "In stock" once set to zero). Without this notice the row
        // simply vanishes from the table with no explanation, which reads as
        // data loss rather than a filter doing its job.
        const stillVisible = index >= 0 && filteredSkus().some(({ v }) => v.id === activeStockId);
        renderSkus();
        if (index >= 0 && !stillVisible) {
            const filterLabel = skuElement('inventoryStockFilter').selectedOptions[0]?.text || 'the current filter';
            showToast(`Stock updated. This item no longer matches "${filterLabel}", so it's hidden — not deleted.`);
        }
    }, 'stockError');
    if (!ok) skuElement('stockDialog').showModal();
});
(async () => { try { await initSidebar(); await refreshInventory(); } catch (e) { skuElement('inventoryError').textContent = e.message; } })();
