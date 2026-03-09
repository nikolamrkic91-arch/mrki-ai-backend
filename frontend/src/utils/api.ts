const API_BASE = '/api/v1';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('mrki_token', token);
    } else {
      localStorage.removeItem('mrki_token');
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('mrki_token');
    }
    return this.token;
  }

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.detail || error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: 'POST', body });
  }

  // Auth
  async login(username: string, password: string) {
    const data = await this.post<{ access_token: string }>('/auth/login', { username, password });
    this.setToken(data.access_token);
    return data;
  }

  async register(username: string, password: string) {
    return this.post<{ success: boolean }>('/auth/register', { username, password });
  }

  logout() {
    this.setToken(null);
  }

  // Health
  async getHealth() {
    return this.get<{ status: string; modules: string[]; uptime: number }>('/health');
  }

  // Core
  async executeTask(task: { name: string; description: string; agent_type?: string; input?: Record<string, unknown> }) {
    return this.post<{ success: boolean; task_id: string; status: string }>('/core/execute', task);
  }

  // Modules health
  async getCoreHealth() {
    return this.get<{ status: string; module: string }>('/core/health');
  }

  async getVisualHealth() {
    return this.get<{ status: string; module: string }>('/visual/health');
  }

  async getMoeHealth() {
    return this.get<{ status: string; module: string }>('/moe/health');
  }

  async getGamedevHealth() {
    return this.get<{ status: string; module: string }>('/gamedev/health');
  }

  async getDevHealth() {
    return this.get<{ status: string; module: string }>('/dev/health');
  }

  // Game dev
  async getEngines() {
    return this.get<{ engines: Array<{ name: string; language: string; templates: string[] }> }>('/gamedev/engines');
  }
}

export const api = new ApiClient();
