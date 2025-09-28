import { HttpClient } from './httpClient';
import { config } from '@/config/env';

// Create a single instance of HttpClient for goals service
export const apiClient = new HttpClient(config.api.goalsServiceUrl || 'http://localhost:8006');
