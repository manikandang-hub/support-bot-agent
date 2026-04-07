import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const getPlugins = () => {
  return api.get('/plugins');
};

export const sendQuery = (pluginId, query, email, conversationId = null) => {
  const payload = {
    plugin_id: pluginId,
    query,
    email,
  };

  // Include conversation_id for follow-up questions
  if (conversationId) {
    payload.conversation_id = conversationId;
  }

  return api.post('/chat', payload);
};

export const prepareTicket = (conversationId, pluginId, email) => {
  return api.post('/prepare-ticket', {
    conversation_id: conversationId,
    plugin_id: pluginId,
    email,
  });
};

export const confirmTicket = (conversationId, pluginId, email, title, description) => {
  return api.post('/confirm-ticket', {
    conversation_id: conversationId,
    plugin_id: pluginId,
    email,
    title,
    description,
  });
};

export default api;
