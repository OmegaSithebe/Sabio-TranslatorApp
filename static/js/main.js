/* ─────────────────────────────────────────────────────────────────────────
   Sabio Language Translator — main.js
   Drives all 4 UI states, API calls, drag-drop, theme, drawer, toast.
   ───────────────────────────────────────────────────────────────────────── */

'use strict';

/* ── State ─────────────────────────────────────────────────────────────── */
let currentSessionId  = null;
let selectedFormat    = 'pdf';
let toastTimer        = null;

/* ── DOM refs ──────────────────────────────────────────────────────────── */
const fileInput       = document.getElementById('fileInput');
const uploadZone      = document.getElementById('uploadZone');
const fileInfoBar     = document.getElementById('fileInfoBar');
const detectedBar     = document.getElementById('detectedBar');
const settingsSection = document.getElementById('settingsSection');
const stateUpload     = document.getElementById('stateUpload');
const stateLoading    = document.getElementById('stateLoading');
const stateResult     = document.getElementById('stateResult');
const targetLang      = document.getElementById('targetLang');
const progressBar     = document.getElementById('progressBar');
const toast           = document.getElementById('toast');
const themeIcon       = document.getElementById('themeIcon');

/* ── Theme ─────────────────────────────────────────────────────────────── */
(function initTheme() {
  let saved = 'light';
  try { saved = localStorage.getItem('sabio-theme') || 'light'; } catch (e) {}
  applyTheme(saved);
})();

function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  if (themeIcon) themeIcon.textContent = (t === 'dark') ? '🌙' : '☀️';
  try { localStorage.setItem('sabio-theme', t); } catch (e) {}
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(cur === 'dark' ? 'light' : 'dark');
}

/* ── Drawer ─────────────────────────────────────────────────────────────── */
function openDrawer() {
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('visible');
  document.body.style.overflow = 'hidden';
}
function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('visible');
  document.body.style.overflow = '';
}

/* ── Toast ──────────────────────────────────────────────────────────────── */
function showToast(msg, duration = 3000) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), duration);
}

/* ── File type icon ─────────────────────────────────────────────────────── */
function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const map = {
    pdf: '📄', docx: '📝', doc: '📝',
    txt: '📃', rtf: '🗒️', odt: '📋',
    pptx: '📊', xlsx: '📊', xls: '📊',
  };
  return map[ext] || '📁';
}

/* ── Upload zone drag-and-drop ──────────────────────────────────────────── */
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    handleFile(files[0]);
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    handleFile(fileInput.files[0]);
  }
});

/* ── Handle file selection ──────────────────────────────────────────────── */
function handleFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  // Optimistically show file name/size while uploading
  document.getElementById('fileTypeIcon').textContent = getFileIcon(file.name);
  document.getElementById('fileName').textContent     = file.name;
  document.getElementById('fileSize').textContent     = formatSize(file.size);
  fileInfoBar.classList.remove('hidden');

  showToast('⏳ Reading file…');

  fetch('/api/upload', { method: 'POST', body: formData })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        showToast('❌ ' + data.error, 4000);
        resetUpload();
        return;
      }

      currentSessionId = data.session_id;

      // Update file info bar
      document.getElementById('fileTypeIcon').textContent = getFileIcon(data.filename);
      document.getElementById('fileName').textContent     = data.filename;
      document.getElementById('fileSize').textContent     = data.size;

      // Show detected language bar
      document.getElementById('detectedLang').textContent    = data.detected_lang;
      document.getElementById('confidenceBadge').textContent = data.confidence + '%';
      detectedBar.classList.remove('hidden');

      // Show settings
      settingsSection.classList.remove('hidden');

      // Pre-select the detected lang in dropdown (don't lock target to source)
      showToast('✅ File ready — ' + data.detected_lang + ' detected');
    })
    .catch((err) => {
      showToast('❌ Upload failed: ' + err.message, 4000);
      resetUpload();
    });
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/* ── Reset upload state ──────────────────────────────────────────────────── */
function resetUpload() {
  fileInput.value = '';
  currentSessionId = null;
  fileInfoBar.classList.add('hidden');
  detectedBar.classList.add('hidden');
  settingsSection.classList.add('hidden');
}

/* ── Start translation ──────────────────────────────────────────────────── */
function startTranslation() {
  if (!currentSessionId) {
    showToast('⚠️ Please upload a document first.', 3000);
    return;
  }
  const lang = targetLang.value;
  if (!lang) {
    showToast('⚠️ Please select a target language.', 3000);
    return;
  }

  const langLabel = targetLang.options[targetLang.selectedIndex]?.text || lang;

  // Switch to loading state
  showState('loading');
  document.getElementById('loadingSub').textContent = 'Translating to ' + langLabel + '…';

  // Reset progress bar animation by toggling class
  progressBar.style.animation = 'none';
  void progressBar.offsetWidth; // reflow
  progressBar.style.animation = '';

  fetch('/api/translate', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ session_id: currentSessionId, target_lang: lang }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        showToast('❌ ' + data.error, 5000);
        showState('upload');
        return;
      }

      // Populate result state
      const pages = data.pages || 1;
      document.getElementById('resultSub').textContent =
        'Translated to ' + data.target_lang + ' · ' + pages + ' page' + (pages !== 1 ? 's' : '');
      document.getElementById('previewText').textContent = data.preview || '(No preview available)';

      // Default format based on original file type
      const ext = guessExtFromSession();
      setDefaultFormat(ext);

      showState('result');
      showToast('✅ Translation complete!');
    })
    .catch((err) => {
      showToast('❌ Translation error: ' + err.message, 5000);
      showState('upload');
    });
}

function guessExtFromSession() {
  // Try to infer original format from the file name shown
  const name = document.getElementById('fileName').textContent || '';
  return name.split('.').pop().toLowerCase() || 'pdf';
}

function setDefaultFormat(ext) {
  const map = { pdf: 'pdf', docx: 'docx', doc: 'docx', xlsx: 'xlsx', xls: 'xlsx', txt: 'txt' };
  const fmt = map[ext] || 'pdf';
  document.querySelectorAll('.fmt-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.fmt === fmt);
  });
  selectedFormat = fmt;
  document.getElementById('dlFmtLabel').textContent = fmt.toUpperCase();
}

/* ── Format selector ────────────────────────────────────────────────────── */
function selectFormat(btn) {
  document.querySelectorAll('.fmt-btn').forEach((b) => b.classList.remove('active'));
  btn.classList.add('active');
  selectedFormat = btn.dataset.fmt;
  document.getElementById('dlFmtLabel').textContent = selectedFormat.toUpperCase();
}

/* ── Download ───────────────────────────────────────────────────────────── */
function downloadFile() {
  if (!currentSessionId) {
    showToast('⚠️ No translation session found.', 3000);
    return;
  }
  showToast('⬇ Preparing download…');
  const url = `/api/download/${currentSessionId}/${selectedFormat}`;
  const a   = document.createElement('a');
  a.href    = url;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/* ── Reset all ───────────────────────────────────────────────────────────── */
function resetAll() {
  currentSessionId = null;
  selectedFormat   = 'pdf';
  resetUpload();
  showState('upload');
}

/* ── State switcher ─────────────────────────────────────────────────────── */
function showState(state) {
  stateUpload.classList.toggle('hidden',  state !== 'upload');
  stateLoading.classList.toggle('hidden', state !== 'loading');
  stateResult.classList.toggle('hidden',  state !== 'result');
}

/* ── Expose globals for inline onclick handlers ─────────────────────────── */
window.toggleTheme     = toggleTheme;
window.openDrawer      = openDrawer;
window.closeDrawer     = closeDrawer;
window.resetUpload     = resetUpload;
window.startTranslation = startTranslation;
window.selectFormat    = selectFormat;
window.downloadFile    = downloadFile;
window.resetAll        = resetAll;
