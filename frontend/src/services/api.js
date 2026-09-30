import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const uploadDocument = async (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percent);
      }
    },
  });
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await api.delete(`/documents/${documentId}`);
  return response.data;
};

export const sendChatMessage = async (question) => {
  const response = await api.post('/chat', { question });
  return response.data;
};

export const generateQuiz = async (topic, difficulty = 'medium', numberOfQuestions = 5) => {
  const response = await api.post('/quiz/generate', {
    topic,
    difficulty,
    number_of_questions: numberOfQuestions,
  });
  return response.data;
};

export const getQuiz = async (quizId) => {
  const response = await api.get(`/quiz/${quizId}`);
  return response.data;
};

export const gradeQuiz = async (quizId, answers) => {
  const response = await api.post('/quiz/grade', {
    quiz_id: quizId,
    answers,
  });
  return response.data;
};

export const getMastery = async () => {
  const response = await api.get('/mastery');
  return response.data;
};

export default api;
