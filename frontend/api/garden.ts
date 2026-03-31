import client from './client';

export interface GardenConfig {
  id: number;
  user_id: number;
  theme: number;
  slug?: string;
  share_token?: string;
  is_share_open: boolean;
  custom_domain?: string;
  custom_html?: string;
  custom_css?: string;
  updated_at: string;
}

export interface SharedGardenResponse {
  owner_nickname: string;
  owner_avatar?: string;
  owner_bio?: string;
  config: GardenConfig;
  thoughts: any[];
}

export const getGardenConfig = async () => {
  const response = await client.get('/garden/config');
  return response.data;
};

export const updateGardenConfig = async (config: Partial<GardenConfig>) => {
  const response = await client.put('/garden/config', config);
  return response.data;
};

export const resetShareToken = async () => {
  const response = await client.post('/garden/config/reset-token');
  return response.data;
};

export const getSharedGardenByToken = async (token: string) => {
  const response = await client.get(`/garden/shared/token/${token}`);
  return response.data;
};

export const getSharedGardenBySlug = async (slug: string) => {
  const response = await client.get(`/garden/shared/slug/${slug}`);
  return response.data;
};

export const updateThoughtPrivacy = async (thoughtId: number, isPublic: boolean) => {
  const response = await client.put(`/thoughts/${thoughtId}`, { is_public: isPublic });
  return response.data;
};
