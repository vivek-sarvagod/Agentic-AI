import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './main-layout/MainLayout';
import HomePage from './pages/HomePage';
import PortfolioPage from './pages/PortfolioPage';
import ContactPage from './pages/ContactPage';
import SurveyComponent from './survey-component/SurveyComponent';
import AISurveyAssistantPage from './pages/AISurveyAssistantPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <MainLayout breadcrumb={[{ label: 'Home' }]}>
              <HomePage />
            </MainLayout>
          }
        />
        <Route
          path="/portfolio"
          element={
            <MainLayout breadcrumb={[{ label: 'Home', path: '/' }, { label: 'Portfolio' }]}>
              <PortfolioPage />
            </MainLayout>
          }
        />
        <Route
          path="/survey"
          element={
            <MainLayout breadcrumb={[{ label: 'Home', path: '/' }, { label: 'Student Survey' }]}>
              <SurveyComponent />
            </MainLayout>
          }
        />
        <Route
          path="/ai-assistant"
          element={
            <MainLayout breadcrumb={[{ label: 'Home', path: '/' }, { label: 'AI Survey Assistant' }]}>
              <AISurveyAssistantPage />
            </MainLayout>
          }
        />
        <Route
          path="/contact"
          element={
            <MainLayout breadcrumb={[{ label: 'Home', path: '/' }, { label: 'Contact' }]}>
              <ContactPage />
            </MainLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
