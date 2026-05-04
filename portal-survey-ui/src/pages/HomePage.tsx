import React from 'react';
import { Link } from 'react-router-dom';
import myPhoto from '../images/my-photo.jpeg';

const HomePage: React.FC = () => {
  return (
    <>
      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="row align-items-center">
          <div className="col-lg-8">
            <h1 className="welcome-title">Welcome to Dashboard</h1>
            <p className="welcome-subtitle">
              Software Architect Intern | Principal Software Engineer | MS in Information Systems
              Candidate
            </p>
            <p className="welcome-text">
              Hi, I&apos;m Vivek Sarvagod, a software architect intern with 18+ years of experience in
              designing scalable enterprise solutions. Currently pursuing my Master&apos;s degree at George
              Mason University with a focus on AI and Machine Learning.
            </p>
            <div className="welcome-buttons">
              <Link to="/portfolio" className="btn btn-teal">
                <i className="bi bi-person-vcard me-2"></i>View Portfolio
              </Link>
              <Link to="/contact" className="btn btn-outline-teal">
                <i className="bi bi-envelope me-2"></i>Contact Me
              </Link>
            </div>
          </div>
          <div className="col-lg-4 text-center">
            <div className="welcome-avatar">
              <img src={myPhoto} alt="Vivek Sarvagod" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="row g-4 mb-4">
        <div className="col-md-6 col-lg-3">
          <div className="stat-card">
            <div className="stat-icon bg-teal">
              <i className="bi bi-briefcase"></i>
            </div>
            <div className="stat-content">
              <h3>18+</h3>
              <p>Years Experience</p>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="stat-card">
            <div className="stat-icon bg-info">
              <i className="bi bi-cloud"></i>
            </div>
            <div className="stat-content">
              <h3>50+</h3>
              <p>Projects Delivered</p>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="stat-card">
            <div className="stat-icon bg-success">
              <i className="bi bi-mortarboard"></i>
            </div>
            <div className="stat-content">
              <h3>MS</h3>
              <p>GMU (In Progress)</p>
            </div>
          </div>
        </div>
        <div className="col-md-6 col-lg-3">
          <div className="stat-card">
            <div className="stat-icon bg-warning">
              <i className="bi bi-award"></i>
            </div>
            <div className="stat-content">
              <h3>10+</h3>
              <p>Certifications</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <h4 className="section-heading mb-4">Quick Navigation</h4>
      <div className="row g-4">
        <div className="col-md-4">
          <Link to="/portfolio" className="nav-card">
            <div className="nav-card-icon">
              <i className="bi bi-person-vcard"></i>
            </div>
            <h5>Portfolio</h5>
            <p>View my professional experience, skills, and education background.</p>
            <span className="nav-card-link">
              View Portfolio <i className="bi bi-arrow-right"></i>
            </span>
          </Link>
        </div>
        <div className="col-md-4">
          <Link to="/survey" className="nav-card">
            <div className="nav-card-icon">
              <i className="bi bi-clipboard-data"></i>
            </div>
            <h5>Student Survey</h5>
            <p>Complete the student survey form for campus feedback.</p>
            <span className="nav-card-link">
              Take Survey <i className="bi bi-arrow-right"></i>
            </span>
          </Link>
        </div>
        <div className="col-md-4">
          <Link to="/contact" className="nav-card">
            <div className="nav-card-icon">
              <i className="bi bi-envelope"></i>
            </div>
            <h5>Contact</h5>
            <p>Get in touch with me for collaborations or inquiries.</p>
            <span className="nav-card-link">
              Contact Me <i className="bi bi-arrow-right"></i>
            </span>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="page-footer mt-4">
        <p className="mb-2">Connect with me</p>
        <a href="https://github.com/vivek-sarvagod?tab=repositories" target="_blank" rel="noreferrer">
          <i className="fa fa-github"></i>
        </a>
        <a href="https://linkedin.com/in/vivek-sarvagod" target="_blank" rel="noreferrer">
          <i className="fa fa-linkedin"></i>
        </a>
        <a href="mailto:viveksarvagod@gmail.com">
          <i className="fa fa-envelope"></i>
        </a>
        <p className="mt-3 mb-0">© 2026 Vivek Sarvagod</p>
      </footer>
    </>
  );
};

export default HomePage;
