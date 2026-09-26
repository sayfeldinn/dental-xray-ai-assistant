/**
 * API client for backend communication
 */
import axios from 'axios';
import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_V1_PREFIX = import.meta.env.VITE_API_V1_PREFIX || '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: `${API_URL}${API_V1_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signUp: (email, password, fullName) => 
    api.post('/auth/signup', { email, password, full_name: fullName }),
  
  signIn: (email, password) => 
    api.post('/auth/signin', { email, password }),
  
  signOut: () => 
    api.post('/auth/signout'),
  
  getCurrentUser: () => 
    api.get('/auth/me'),
};

// Patient API
export const patientAPI = {
  list: (params) => 
    api.get('/patients', { params }),
  
  get: (id) => 
    api.get(`/patients/${id}`),
  
  create: (data) => 
    api.post('/patients', data),
  
  update: (id, data) => 
    api.put(`/patients/${id}`, data),
  
  delete: (id) => 
    api.delete(`/patients/${id}`),
};

// Scan API
export const scanAPI = {
  list: (params) => 
    api.get('/scans', { params }),
  
  get: (id) => 
    api.get(`/scans/${id}`),
  
  upload: (formData, params) => 
    api.post('/scans/upload', formData, {
      params,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  update: (id, data) => 
    api.put(`/scans/${id}`, data),
  
  delete: (id) => 
    api.delete(`/scans/${id}`),
};

// Recommendation API
export const recommendationAPI = {
  getTreatment: (finding, patientId) => 
    api.post('/recommendations/treatment', { finding, patient_id: patientId }),
  
  checkContraindication: (drugName, patientId) => 
    api.post('/recommendations/check-contraindication', { 
      drug_name: drugName, 
      patient_id: patientId 
    }),
  
  getDrugs: () => 
    api.get('/recommendations/drugs'),
  
  getFindingMappings: () => 
    api.get('/recommendations/finding-mappings'),
};

export default api;
