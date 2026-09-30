import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import ChatPage from './pages/ChatPage';
import QuizPage from './pages/QuizPage';
import ResultsPage from './pages/ResultsPage';
import MasteryPage from './pages/MasteryPage';
import { getDocuments, getMastery, getHealth } from './services/api';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [documents, setDocuments] = useState([]);
  const [masteryTopics, setMasteryTopics] = useState([]);
  const [healthInfo, setHealthInfo] = useState(null);
  const [recentQuizResult, setRecentQuizResult] = useState(null);
  const [recentScore, setRecentScore] = useState(null);

  const fetchAppData = async () => {
    try {
      const [docsData, masteryData, healthData] = await Promise.allSettled([
        getDocuments(),
        getMastery(),
        getHealth()
      ]);

      if (docsData.status === 'fulfilled') {
        setDocuments(docsData.value);
      }
      if (masteryData.status === 'fulfilled' && masteryData.value?.topics) {
        setMasteryTopics(masteryData.value.topics);
      }
      if (healthData.status === 'fulfilled') {
        setHealthInfo(healthData.value);
      }
    } catch (err) {
      console.error('Error fetching portal data:', err);
    }
  };

  useEffect(() => {
    fetchAppData();
  }, []);

  const handleQuizFinished = (resultPayload) => {
    setRecentQuizResult(resultPayload);
    if (resultPayload?.results?.percentage !== undefined) {
      setRecentScore(resultPayload.results.percentage);
    }
    fetchAppData(); // Refresh mastery
    setActivePage('results');
  };

  const getPageTitle = () => {
    switch (activePage) {
      case 'dashboard':
        return 'Student Learning Dashboard';
      case 'upload':
        return 'Course Materials & Document Ingestion';
      case 'chat':
        return 'AI Study Tutor & Grounded Q&A';
      case 'quiz':
        return 'Adaptive Topic Quiz';
      case 'results':
        return 'Quiz Assessment & AI Diagnostic';
      case 'mastery':
        return 'Per-Topic Mastery Tracking';
      default:
        return 'Smart Study Portal';
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        hasResults={Boolean(recentQuizResult)}
      />

      <div className="main-content">
        <Header
          title={getPageTitle()}
          healthInfo={healthInfo}
        />

        <main className="content-body">
          {activePage === 'dashboard' && (
            <DashboardPage
              documents={documents}
              masteryTopics={masteryTopics}
              recentScore={recentScore}
              onNavigate={(page) => setActivePage(page)}
            />
          )}

          {activePage === 'upload' && (
            <UploadPage
              documents={documents}
              onRefreshDocuments={fetchAppData}
            />
          )}

          {activePage === 'chat' && (
            <ChatPage
              documents={documents}
            />
          )}

          {activePage === 'quiz' && (
            <QuizPage
              documents={documents}
              onQuizFinished={handleQuizFinished}
            />
          )}

          {activePage === 'results' && (
            <ResultsPage
              resultsData={recentQuizResult}
              onRetake={() => setActivePage('quiz')}
              onNavigate={(page) => setActivePage(page)}
            />
          )}

          {activePage === 'mastery' && (
            <MasteryPage
              masteryTopics={masteryTopics}
              onNavigate={(page) => setActivePage(page)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
