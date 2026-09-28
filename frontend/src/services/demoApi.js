/**
 * Demo-mode API adapter.
 *
 * Installed as the axios adapter when VITE_DEMO_MODE=true, so every page works
 * without the FastAPI backend or Supabase. Routes mirror what the frontend
 * actually calls (see src/services/api.js and src/pages/*).
 */
import {
  DEMO_IMAGE,
  buildRecommendations,
  getPatients,
  getPredictions,
  getScans,
} from './demoData';

const DELAY_MS = 140;

const patients = getPatients();
const scans = getScans();
const predictionsByScan = new Map(
  scans.map((scan) => [scan.id, getPredictions(scan.id)])
);

let idSeq = 900;

function normalizePath(config) {
  let url = config.url || '';
  if (/^https?:\/\//.test(url)) {
    url = new URL(url).pathname;
  }
  // Drop the baseURL prefix when axios has already merged it in.
  if (config.baseURL && url.startsWith(config.baseURL)) {
    url = url.slice(config.baseURL.length);
  }
  url = url.split('?')[0];
  if (url.length > 1 && url.endsWith('/')) url = url.slice(0, -1);
  return url;
}

function parseBody(config) {
  if (!config.data) return {};
  if (typeof config.data === 'string') {
    try {
      return JSON.parse(config.data);
    } catch {
      return {};
    }
  }
  return config.data;
}

function httpError(config, status, detail) {
  const error = new Error(typeof detail === 'string' ? detail : 'Request failed');
  error.isAxiosError = true;
  error.config = config;
  error.response = { status, data: { detail }, config, headers: {} };
  return error;
}

function notFound(config, path) {
  return httpError(config, 404, `Demo mode has no handler for ${path}`);
}

function listPatients(config) {
  const search = (config.params?.search || '').toLowerCase().trim();
  const filtered = patients.filter((p) => {
    if (!search) return true;
    const haystack = `${p.first_name} ${p.last_name} ${p.email}`.toLowerCase();
    return haystack.includes(search);
  });
  return {
    patients: filtered,
    total: filtered.length,
    page: 1,
    page_size: filtered.length || 1,
  };
}

function listScans() {
  return {
    scans: scans.map((s) => ({ ...s })),
    total: scans.length,
    page: 1,
    page_size: scans.length || 1,
  };
}

function predictionsFor(scanId) {
  return (predictionsByScan.get(scanId) || []).map((p) => ({ ...p }));
}

function handle(config) {
  const method = (config.method || 'get').toLowerCase();
  const path = normalizePath(config);
  const body = parseBody(config);
  const segments = path.split('/').filter(Boolean); // e.g. ['api','v1','scans','s-001']

  // Strip the version prefix if it ever arrives inline.
  if (segments[0] === 'api' && segments[1] === 'v1') segments.splice(0, 2);

  const [root, id, sub] = segments;

  if (root === 'patients') {
    if (method === 'get' && !id) return { status: 200, data: listPatients(config) };
    if (method === 'get' && id) {
      const patient = patients.find((p) => p.id === id);
      return patient ? { status: 200, data: { ...patient } } : { error: notFound(config, path) };
    }
    if (method === 'post' && !id) {
      const created = {
        id: `p-${++idSeq}`,
        contact_number: body.phone || '',
        age: body.date_of_birth
          ? Math.max(
              0,
              new Date().getFullYear() - new Date(body.date_of_birth).getFullYear()
            )
          : null,
        medical_history: [],
        current_medications: body.current_medications || [],
        medical_conditions: body.medical_conditions || [],
        ...body,
      };
      patients.unshift(created);
      return { status: 201, data: { ...created } };
    }
  }

  if (root === 'scans') {
    if (method === 'get' && id && sub === 'predictions') {
      return { status: 200, data: predictionsFor(id) };
    }
    if (method === 'get' && id) {
      const scan = scans.find((s) => s.id === id);
      return scan ? { status: 200, data: { ...scan } } : { error: notFound(config, path) };
    }
    if (method === 'get' && !id) return { status: 200, data: listScans() };
    if (method === 'post') {
      const patient = patients.find((p) => p.id === body.patient_id);
      const created = {
        id: `s-${++idSeq}`,
        patient_id: body.patient_id,
        patient_name: patient ? `${patient.first_name} ${patient.last_name}` : undefined,
        scan_type: body.scan_type || 'panoramic',
        image_url: body.image_url || DEMO_IMAGE,
        status: body.status || 'pending',
        notes: body.notes || null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      scans.unshift(created);
      predictionsByScan.set(created.id, []);
      return { status: 201, data: { ...created } };
    }
  }

  if (root === 'ml' && id === 'infer' && method === 'post') {
    const scan = scans.find((s) => s.id === sub);
    if (!scan) return { error: notFound(config, path) };
    scan.status = 'completed';
    scan.updated_at = new Date().toISOString();
    if (!predictionsByScan.get(scan.id)?.length) {
      predictionsByScan.set(scan.id, getPredictions('s-001'));
    }
    return {
      status: 200,
      data: { scan_id: scan.id, status: 'completed', findings: predictionsFor(scan.id) },
    };
  }

  if (root === 'recommendations' && (id === 'drugs' || id === 'finding-mappings')) {
    return { status: 200, data: id === 'drugs' ? { drugs: [] } : { mappings: [] } };
  }

  if (root === 'recommendations' && id && method === 'get') {
    const scan = scans.find((s) => s.id === id);
    if (!scan) return { error: notFound(config, path) };
    const patient = patients.find((p) => p.id === scan.patient_id) || {};
    const { recommendations } = buildRecommendations(patient, predictionsFor(scan.id));
    return { status: 200, data: recommendations };
  }

  if (root === 'feedback' && method === 'post') {
    const preds = predictionsByScan.get(body.scan_id) || [];
    const pred = preds.find((p) => p.id === body.prediction_id);
    if (pred) pred.confirmed = Boolean(body.is_correct);
    return { status: 201, data: { id: `fb-${++idSeq}`, ...body } };
  }

  if (root === 'treatments' && method === 'post') {
    return { status: 201, data: { id: `t-${++idSeq}`, ...body } };
  }

  if (root === 'auth') {
    if (method === 'get' && id === 'me') {
      return {
        status: 200,
        data: { id: 'demo-user', email: 'demo@dentalai.local', full_name: 'Demo Dentist' },
      };
    }
    return { status: 200, data: { user: { id: 'demo-user' }, session: null } };
  }

  return { error: notFound(config, path) };
}

/**
 * Axios adapter: resolves every request from the in-memory demo store.
 */
export function demoAdapter(config) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      let result;
      try {
        result = handle(config);
      } catch (err) {
        reject(err);
        return;
      }

      if (result.error) {
        reject(result.error);
        return;
      }

      resolve({
        data: result.data,
        status: result.status,
        statusText: result.status === 201 ? 'Created' : 'OK',
        headers: { 'content-type': 'application/json' },
        config,
        request: {},
      });
    }, DELAY_MS);
  });
}
