import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import MeetingsList from './pages/MeetingsList';
import MeetingDetail from './pages/MeetingDetail';
import JiraSettings from './pages/JiraSettings';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/meetings" element={<MeetingsList />} />
          <Route path="/meetings/:jobId" element={<MeetingDetail />} />
          <Route path="/settings" element={<JiraSettings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
