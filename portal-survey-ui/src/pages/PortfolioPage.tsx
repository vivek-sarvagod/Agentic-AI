import React from 'react';
import myPhoto from '../images/my-photo.jpeg';

interface SkillItem {
  label: string;
  pct: number;
}

const SKILLS: SkillItem[] = [
  { label: 'Cloud Architecture (Azure & AWS)', pct: 95 },
  { label: '.NET Core / C#', pct: 95 },
  { label: 'Python / Django / FastAPI', pct: 90 },
  { label: 'React / Angular / TypeScript', pct: 90 },
  { label: 'Data Engineering & BI', pct: 85 },
];

const PortfolioPage: React.FC = () => {
  return (
    <div className="portfolio-container">
      <div className="row g-4">
        {/* ── Left Column: Profile Card ── */}
        <div className="col-lg-4">
          <div className="profile-card">
            <div className="profile-header">
              <img src={myPhoto} alt="Profile Photo" />
              <div className="profile-header-overlay">
                <h2>Vivek Sarvagod</h2>
              </div>
            </div>
            <div className="profile-body">
              <div className="profile-info-item">
                <i className="fa fa-briefcase"></i>
                <span>Software Architect Intern</span>
              </div>
              <div className="profile-info-item">
                <i className="fa fa-home"></i>
                <span>Fairfax, Virginia, USA</span>
              </div>
              <div className="profile-info-item">
                <i className="fa fa-envelope"></i>
                <span>viveksarvagod@gmail.com</span>
              </div>
              <div className="profile-info-item">
                <i className="fa fa-linkedin"></i>
                <span>linkedin.com/in/vivek-sarvagod</span>
              </div>

              <hr />

              <h5 className="mb-3">
                <i className="fa fa-asterisk me-2" style={{ color: 'var(--teal)' }}></i>
                Core Skills
              </h5>
              {SKILLS.map((skill) => (
                <div className="skill-item" key={skill.label}>
                  <label>{skill.label}</label>
                  <div className="skill-bar">
                    <div className="skill-progress" style={{ width: `${skill.pct}%` }}>
                      {skill.pct}%
                    </div>
                  </div>
                </div>
              ))}

              <hr />

              <h5 className="mb-3">
                <i className="fa fa-graduation-cap me-2" style={{ color: 'var(--teal)' }}></i>
                Focus Areas
              </h5>
              <div>
                {[
                  'AI & Machine Learning',
                  'Graph Representation Learning',
                  'Healthcare Systems',
                  'Distributed Systems',
                ].map((tag) => (
                  <span className="focus-tag" key={tag}>
                    <i className="bi bi-check-circle-fill"></i>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Right Column: Content Cards ── */}
        <div className="col-lg-8">
          {/* Professional Summary */}
          <div className="content-card">
            <div className="content-card-header">
              <i className="fa fa-user"></i>
              <h3>Professional Summary</h3>
            </div>
            <div className="content-card-body">
              <p style={{ lineHeight: 1.8, margin: 0 }}>
                Software Architect Engineer with 18+ years of experience designing scalable
                enterprise and healthcare systems. Expertise in cloud-native architecture,
                full-stack development, and data-driven platforms across Azure and AWS. Currently
                pursuing a Master&apos;s degree at George Mason University with a focus on AI, Graph
                Representation Learning, and next-generation intelligent systems. Passionate about
                leading high-performing teams and building impactful technology solutions.
              </p>
            </div>
          </div>

          {/* Work Experience */}
          <div className="content-card">
            <div className="content-card-header">
              <i className="fa fa-suitcase"></i>
              <h3>Work Experience</h3>
            </div>
            <div className="content-card-body">
              {/* <div className="experience-item">
                <h5>Database Architect Intern</h5>
                <div className="period">
                  <i className="fa fa-calendar"></i>
                  June 2025 – Present
                </div>
                <ul>
                  <li>
                    Designed and implemented Role-Based Access Control (RBAC) systems for secure
                    user management
                  </li>
                  <li>
                    Optimized relational data models in MySQL; implemented indexing strategies for
                    improved query performance
                  </li>
                  <li>Worked on microservices, authentication systems, and data workflows</li>
                </ul>
              </div> */}

              <div className="experience-item">
                <h5>Software Architect Intern</h5>
                <div className="period">
                  <i className="fa fa-calendar"></i>
                  June 2025 – Present
                </div>
                <ul>
                  <li>Contributed to cloud-based application architecture</li>
                  <li>Improved backend APIs performance and scalability</li>
                  <li>Worked on microservices, authentication systems, and data workflows</li>
                </ul>
              </div>

              <div className="experience-item">
                <h5>Graduate Teaching Assistant</h5>
                <div className="period">
                  <i className="fa fa-calendar"></i>
                  Present (George Mason University)
                </div>
                <ul>
                  <li>
                    Support undergraduate and graduate courses in Information Technology and
                    Information Systems, providing instructional assistance for classes of 100+
                    students.
                  </li>
                  <li>
                    Evaluate assignments, quizzes, examinations, and projects with comprehensive,
                    timely, and constructive feedback aligned with learning objectives.
                  </li>
                  <li>
                    Conduct weekly office hours and review sessions to reinforce course concepts and
                    prepare students for examinations.
                  </li>
                  <li>
                    Collaborate with faculty on instructional activities, grading rubric development,
                    and course logistics management.
                  </li>
                </ul>
              </div>

              <div className="experience-item">
                <h5>Principal Software Engineer</h5>
                <div className="period">
                  <i className="fa fa-calendar"></i>
                  17+ Years Experience
                </div>
                <ul>
                  <li>
                    Led cross-functional engineering teams delivering enterprise-grade healthcare
                    systems
                  </li>
                  <li>Architected cloud-native microservices on Azure &amp; AWS</li>
                  <li>
                    Designed secure patient data management platforms ensuring compliance &amp;
                    performance
                  </li>
                  <li>
                    Implemented CI/CD pipelines, DevOps automation, and scalable distributed systems
                  </li>
                  <li>Mentored engineers and drove Agile, TDD, and BDD best practices</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Education */}
          <div className="content-card">
            <div className="content-card-header">
              <i className="fa fa-certificate"></i>
              <h3>Education</h3>
            </div>
            <div className="content-card-body">
              <div className="experience-item">
                <h5>Master&apos;s Degree (MS)</h5>
                <div className="period">
                  <i className="fa fa-calendar"></i>
                  May 2026
                </div>
                <p style={{ margin: 0 }}>
                  Information Systems | 3.8 GPA | George Mason University, Fairfax, VA
                </p>
                <p style={{ margin: 0 }}>Focus on AI, Machine Learning &amp; Advanced Computing</p>
              </div>
              <div className="experience-item">
                <h5>Bachelor&apos;s Degree in Engineering</h5>
                <p style={{ margin: 0 }}>Computer Science &amp; Engineering</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="page-footer">
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
    </div>
  );
};

export default PortfolioPage;
