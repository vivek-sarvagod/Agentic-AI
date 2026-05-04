import React, { useState } from 'react';

interface ContactForm {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
  consent: boolean;
}

const EMPTY_FORM: ContactForm = {
  name: '',
  email: '',
  phone: '',
  subject: '',
  message: '',
  consent: false,
};

interface AlertState {
  message: string;
  type: 'success' | 'danger' | '';
}

const ContactPage: React.FC = () => {
  const [formData, setFormData] = useState<ContactForm>(EMPTY_FORM);
  const [alert, setAlert] = useState<AlertState>({ message: '', type: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const target = e.target as HTMLInputElement;
    setFormData((prev) => ({
      ...prev,
      [target.name]: target.type === 'checkbox' ? target.checked : target.value,
    }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setAlert({ message: '', type: '' });
    setSubmitting(true);

    // Simulate a brief send delay (no real backend for contact form)
    setTimeout(() => {
      setAlert({
        message:
          '<i class="bi bi-check-circle-fill me-2"></i><strong>Message Sent!</strong> Thank you for reaching out. I will get back to you soon!',
        type: 'success',
      });
      setFormData(EMPTY_FORM);
      setSubmitting(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 600);
  };

  return (
    <div className="contact-container">
      <div className="row g-4">
        {/* ── Left Column: Contact Info ── */}
        <div className="col-lg-4">
          <div className="contact-info-card">
            <h3>
              <i className="bi bi-geo-alt-fill me-2"></i>Get in Touch
            </h3>
            <p className="mb-4">
              Feel free to reach out to me for collaborations, opportunities, or just to say hello!
            </p>

            <div className="contact-info-item">
              <div className="contact-icon">
                <i className="bi bi-geo-alt"></i>
              </div>
              <div className="contact-details">
                <h6>Address</h6>
                <p>
                  Fairfax, Virginia
                  <br />
                  United States
                </p>
              </div>
            </div>

            <div className="contact-info-item">
              <div className="contact-icon">
                <i className="bi bi-envelope"></i>
              </div>
              <div className="contact-details">
                <h6>Email</h6>
                <p>viveksarvagod@gmail.com</p>
              </div>
            </div>

            <div className="contact-info-item">
              <div className="contact-icon">
                <i className="bi bi-telephone"></i>
              </div>
              <div className="contact-details">
                <h6>Phone</h6>
                <p>+1 (667) 369-5838</p>
              </div>
            </div>

            <div className="contact-info-item">
              <div className="contact-icon">
                <i className="bi bi-clock"></i>
              </div>
              <div className="contact-details">
                <h6>Availability</h6>
                <p>Mon - Fri: 9:00 AM - 6:00 PM EST</p>
              </div>
            </div>

            <hr className="my-4" />

            <h5 className="mb-3">Connect on Social</h5>
            <div className="social-links">
              <a
                href="https://github.com/vivek-sarvagod?tab=repositories"
                target="_blank"
                rel="noreferrer"
                className="social-link"
                title="GitHub"
              >
                <i className="bi bi-github"></i>
              </a>
              <a
                href="https://linkedin.com/in/vivek-sarvagod"
                target="_blank"
                rel="noreferrer"
                className="social-link"
                title="LinkedIn"
              >
                <i className="bi bi-linkedin"></i>
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="social-link"
                title="Twitter"
              >
                <i className="bi bi-twitter-x"></i>
              </a>
              <a href="mailto:viveksarvagod@gmail.com" className="social-link" title="Email">
                <i className="bi bi-envelope-fill"></i>
              </a>
            </div>
          </div>
        </div>

        {/* ── Right Column: Contact Form ── */}
        <div className="col-lg-8">
          <div className="contact-form-card">
            <div className="contact-form-header">
              <h3>
                <i className="bi bi-send me-2"></i>Send a Message
              </h3>
              <p>Have a question or want to work together? Fill out the form below.</p>
            </div>

            {alert.type && (
              <div
                className={`alert alert-${alert.type} mb-4`}
                role="alert"
                dangerouslySetInnerHTML={{ __html: alert.message }}
              />
            )}

            <form onSubmit={handleSubmit} noValidate>
              <div className="row g-3">
                <div className="col-md-6">
                  <label htmlFor="contactName" className="form-label">
                    Full Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    id="contactName"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="col-md-6">
                  <label htmlFor="contactEmail" className="form-label">
                    Email Address <span className="required">*</span>
                  </label>
                  <input
                    type="email"
                    className="form-control"
                    id="contactEmail"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    placeholder="your-email@example.com"
                  />
                </div>
                <div className="col-md-6">
                  <label htmlFor="contactPhone" className="form-label">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    className="form-control"
                    id="contactPhone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="(123) 456-7890"
                  />
                </div>
                <div className="col-md-6">
                  <label htmlFor="contactSubject" className="form-label">
                    Subject <span className="required">*</span>
                  </label>
                  <select
                    className="form-select"
                    id="contactSubject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                  >
                    <option value="">-- Select a subject --</option>
                    <option value="general">General Inquiry</option>
                    <option value="collaboration">Collaboration Opportunity</option>
                    <option value="job">Job Opportunity</option>
                    <option value="consulting">Consulting Request</option>
                    <option value="feedback">Feedback</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="col-12">
                  <label htmlFor="contactMessage" className="form-label">
                    Message <span className="required">*</span>
                  </label>
                  <textarea
                    className="form-control"
                    id="contactMessage"
                    name="message"
                    rows={6}
                    value={formData.message}
                    onChange={handleChange}
                    required
                    placeholder="Write your message here..."
                  />
                </div>
                <div className="col-12">
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="contactConsent"
                      name="consent"
                      checked={formData.consent}
                      onChange={handleChange}
                    />
                    <label className="form-check-label" htmlFor="contactConsent">
                      I agree to be contacted regarding my inquiry
                    </label>
                  </div>
                </div>
                <div className="col-12">
                  <div className="d-flex gap-3 mt-3">
                    <button type="submit" className="btn btn-teal" disabled={submitting}>
                      {submitting ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <i className="bi bi-send me-2"></i>Send Message
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => setFormData(EMPTY_FORM)}
                    >
                      <i className="bi bi-x-circle me-2"></i>Clear Form
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>

          {/* Info Mini Cards */}
          <div className="row g-4 mt-2">
            <div className="col-md-6">
              <div className="info-mini-card">
                <div className="info-mini-icon bg-teal">
                  <i className="bi bi-lightning-charge"></i>
                </div>
                <div className="info-mini-content">
                  <h5>Quick Response</h5>
                  <p>I typically respond within 24-48 hours</p>
                </div>
              </div>
            </div>
            <div className="col-md-6">
              <div className="info-mini-card">
                <div className="info-mini-icon bg-info">
                  <i className="bi bi-shield-check"></i>
                </div>
                <div className="info-mini-content">
                  <h5>Privacy Protected</h5>
                  <p>Your information is kept confidential</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Map Placeholder */}
      <div className="map-section mt-4">
        <div className="map-placeholder">
          <i className="bi bi-geo-alt-fill"></i>
          <h4>Fairfax, Virginia</h4>
          <p>Greater Washington D.C. Metropolitan Area</p>
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

export default ContactPage;
