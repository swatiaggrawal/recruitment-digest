const MONTHS = {
  jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
  jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
};

// Tries a handful of common date formats seen on Indian government sites.
function parseFlexibleDate(str) {
  if (!str) return null;
  const s = str.trim();

  // DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
  let m = s.match(/^(\d{1,2})[\-\/.](\d{1,2})[\-\/.](\d{4})$/);
  if (m) return new Date(+m[3], +m[2] - 1, +m[1]);

  // DD Mon YYYY  (e.g. "12 Jul 2026")
  m = s.match(/^(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})$/);
  if (m) {
    const monthKey = m[2].slice(0, 3).toLowerCase();
    if (monthKey in MONTHS) return new Date(+m[3], MONTHS[monthKey], +m[1]);
  }

  const fallback = new Date(s);
  return isNaN(fallback) ? null : fallback;
}

function daysUntil(date) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((date - today) / 86400000);
}

function urgencyBucket(lastDateStr) {
  const date = parseFlexibleDate(lastDateStr);
  if (!date) return { bucket: 'unknown', days: null };
  const days = daysUntil(date);
  if (days < 0) return { bucket: 'unknown', days };       // already past, treat as unclear
  if (days <= 5) return { bucket: 'urgent', days };
  if (days <= 14) return { bucket: 'caution', days };
  return { bucket: 'open', days };
}

function daysLabel(bucket, days) {
  if (bucket === 'unknown' || days === null) return 'No clear date';
  if (days === 0) return 'Closes today';
  if (days === 1) return '1 day left';
  return `${days} days left`;
}

let ALL_JOBS = [];
let activeFilter = 'all';

async function loadData() {
  const res = await fetch('data.json', { cache: 'no-store' });
  const data = await res.json();

  const updated = new Date(data.last_updated);
  document.getElementById('updated-text').textContent =
    'Updated ' + updated.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  document.getElementById('count-text').textContent = `${data.count} listings`;

  ALL_JOBS = data.jobs.map(job => {
    const { bucket, days } = urgencyBucket(job.last_date);
    return { ...job, urgencyBucket: bucket, daysLeft: days };
  });

  render();
}

function render() {
  const query = document.getElementById('search-input').value.trim().toLowerCase();
  const sortBy = document.getElementById('sort-select').value;

  let jobs = ALL_JOBS.filter(j => {
    if (activeFilter !== 'all' && j.urgencyBucket !== activeFilter) return false;
    if (!query) return true;
    return j.organisation.toLowerCase().includes(query) || j.post.toLowerCase().includes(query);
  });

  jobs.sort((a, b) => {
    if (sortBy === 'org') return a.organisation.localeCompare(b.organisation);
    if (sortBy === 'issued') {
      const da = parseFlexibleDate(a.issued_date), db = parseFlexibleDate(b.issued_date);
      return (db || 0) - (da || 0);
    }
    // deadline: soonest first, unknowns last
    const da = a.daysLeft === null ? Infinity : a.daysLeft;
    const db = b.daysLeft === null ? Infinity : b.daysLeft;
    return da - db;
  });

  const list = document.getElementById('job-list');
  const empty = document.getElementById('empty-state');
  list.innerHTML = '';

  if (jobs.length === 0) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  for (const job of jobs) {
    list.appendChild(renderCard(job));
  }
}

function renderCard(job) {
  const li = document.createElement('li');
  li.className = `job-card ${job.urgencyBucket}`;

  const label = daysLabel(job.urgencyBucket, job.daysLeft);

  li.innerHTML = `
    <div class="job-card-top">
      <div>
        <div class="job-org">${escapeHtml(job.organisation)}</div>
        <div class="job-post">${escapeHtml(job.post)}</div>
      </div>
      <span class="days-chip ${job.urgencyBucket}">${label}</span>
    </div>
    <div class="job-meta">
      <span>Issued: ${escapeHtml(job.issued_date || '—')}</span>
      <span>Last date: ${escapeHtml(job.last_date || '—')}</span>
      <span>${escapeHtml(job.appointment_method || '')}</span>
    </div>
    <div class="job-actions">
      ${job.department_url
        ? `<a class="btn btn-primary" href="${job.department_url}" target="_blank" rel="noopener">Department site</a>`
        : ''}
      <a class="btn btn-secondary" href="${job.search_url}" target="_blank" rel="noopener">Find notification</a>
    </div>
  `;
  return li;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

document.getElementById('search-input').addEventListener('input', render);
document.getElementById('sort-select').addEventListener('change', render);
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeFilter = chip.dataset.filter;
    render();
  });
});

loadData().catch(err => {
  document.getElementById('updated-text').textContent = 'Could not load data.json';
  console.error(err);
});
