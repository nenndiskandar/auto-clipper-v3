/* Auto Clipper Shared UI Helpers (Toast, Confirm, Disk) */

/* Force dark only (toggle removed) */
document.documentElement.classList.add('dark');
document.documentElement.style.colorScheme = 'dark';
try { localStorage.removeItem('ac' + '_theme'); } catch (e) {}

/* ── Toast Notification ── */
function showToast(message, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  const iconCls = type === 'success' ? 'bi-check-circle-fill text-emerald-400' : type === 'error' ? 'bi-x-circle-fill text-rose-400' : 'bi-info-circle text-sky-400';
  toast.innerHTML = '<i class="bi ' + iconCls + '"></i><span></span>';
  toast.lastElementChild.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Custom Confirm Modal ── */
function showConfirm(title, message) {
  return new Promise(resolve => {
    let modal = document.querySelector('.confirm-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'confirm-modal';
      modal.innerHTML = '<div class="confirm-box">' +
        '<div class="confirm-title"></div>' +
        '<div class="confirm-msg"></div>' +
        '<div class="confirm-actions">' +
        '<button class="btn-cancel" type="button">Batal</button>' +
        '<button class="btn-confirm" type="button">Konfirmasi</button>' +
        '</div></div>';
      document.body.appendChild(modal);
      modal.querySelector('.btn-cancel').addEventListener('click', () => {
        modal.classList.remove('open');
        const r = modal._currentResolve; modal._currentResolve = null;
        if (r) r(false);
      });
      modal.querySelector('.btn-confirm').addEventListener('click', () => {
        modal.classList.remove('open');
        const r = modal._currentResolve; modal._currentResolve = null;
        if (r) r(true);
      });
      modal.addEventListener('click', e => {
        if (e.target === modal) {
          modal.classList.remove('open');
          const r = modal._currentResolve; modal._currentResolve = null;
          if (r) r(false);
        }
      });
    }
    modal._currentResolve = resolve;
    modal.querySelector('.confirm-title').textContent = title;
    modal.querySelector('.confirm-msg').textContent = message;
    modal.classList.add('open');
  });
}

/* ── Disk Space Widget ── */
async function refreshDisk() {
  const bar = document.querySelector('.disk-fill');
  const label = document.querySelector('.disk-label');
  if (!bar || !label) return;
  try {
    const r = await fetch('/api/disk');
    const d = await r.json();
    const pct = Math.round(d.usedPercent || 0);
    const gb = v => (v / (1024 * 1024 * 1024)).toFixed(1);
    label.innerHTML = '<i class="bi bi-hdd-stack text-sky-400"></i> ' + gb(d.used) + ' / ' + gb(d.total) + ' GB (' + pct + '%)';
    bar.style.width = pct + '%';
    bar.className = 'disk-fill' + (pct >= 90 ? ' danger' : pct >= 80 ? ' warn' : '');
  } catch {
    label.innerHTML = '<i class="bi bi-hdd-stack text-sky-400"></i> disk: n/a';
  }
}

// Lifecycle hooks
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    refreshDisk();
    setInterval(refreshDisk, 30000);
  });
} else {
  refreshDisk();
  setInterval(refreshDisk, 30000);
}
