import React, { useState, useEffect, useCallback } from 'react';
import { surveyApi, Survey, SurveyData } from '../services/surveyApi';

type ViewMode = 'form' | 'list';

interface AlertState {
  message: string;
  type: 'success' | 'danger' | '';
}

const CAMPUS_LIKES_OPTIONS = [
  { value: 'students', label: 'Students', icon: 'bi-people' },
  { value: 'location', label: 'Location', icon: 'bi-geo-alt' },
  { value: 'campus', label: 'Campus', icon: 'bi-building' },
  { value: 'atmosphere', label: 'Atmosphere', icon: 'bi-sun' },
  { value: 'dorm_rooms', label: 'Dorm Rooms', icon: 'bi-house-door' },
  { value: 'sports', label: 'Sports', icon: 'bi-trophy' },
];

const INTEREST_SOURCE_OPTIONS = [
  { value: 'friends', label: 'Friends', icon: 'bi-people-fill' },
  { value: 'television', label: 'Television', icon: 'bi-tv' },
  { value: 'internet', label: 'Internet', icon: 'bi-globe' },
  { value: 'other', label: 'Other', icon: 'bi-three-dots' },
];

const EMPTY_FORM: SurveyData = {
  firstName: '',
  lastName: '',
  streetAddress: '',
  city: '',
  state: '',
  zip: '',
  telephone: '',
  email: '',
  surveyDate: new Date().toISOString().split('T')[0],
  campusLikes: [],
  interestSource: '',
  recommendation: '',
  raffle: '',
  comments: '',
};

const SurveyComponent: React.FC = () => {
  const [view, setView] = useState<ViewMode>('form');
  const [formData, setFormData] = useState<SurveyData>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [alert, setAlert] = useState<AlertState>({ message: '', type: '' });
  const [raffleError, setRaffleError] = useState('');
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);

  const fetchSurveys = useCallback(async () => {
    setListLoading(true);
    try {
      const data = await surveyApi.getAll();
      setSurveys(data);
    } catch (err) {
      showAlert(`Failed to load surveys: ${(err as Error).message}`, 'danger');
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    if (view === 'list') {
      fetchSurveys();
    }
  }, [view, fetchSurveys]);

  const showAlert = (message: string, type: 'success' | 'danger') => {
    setAlert({ message, type });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const clearAlert = () => setAlert({ message: '', type: '' });

  // ── Form field handlers ──────────────────────────────────────────────────

  const handleTextChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      campusLikes: checked
        ? [...prev.campusLikes, value]
        : prev.campusLikes.filter((v) => v !== value),
    }));
  };

  // ── Raffle validation ───────────────────────────────────────────────────

  const validateRaffle = (input: string): boolean => {
    if (!input || input.trim() === '') {
      setRaffleError('');
      return true;
    }
    const numbers = input
      .split(',')
      .map((n) => n.trim())
      .filter((n) => n !== '');
    if (numbers.length < 10) {
      setRaffleError('Please enter at least 10 numbers.');
      return false;
    }
    for (const num of numbers) {
      const n = parseInt(num, 10);
      if (isNaN(n) || n < 1 || n > 100) {
        setRaffleError(`Invalid number: "${num}". Please enter numbers between 1 and 100.`);
        return false;
      }
    }
    setRaffleError('');
    return true;
  };

  // ── Submit ──────────────────────────────────────────────────────────────

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearAlert();

    if (!validateRaffle(formData.raffle ?? '')) return;

    setLoading(true);
    try {
      if (editingId !== null) {
        await surveyApi.update(editingId, formData);
        showAlert(
          '<i class="bi bi-check-circle-fill me-2"></i><strong>Success!</strong> Survey updated successfully.',
          'success'
        );
      } else {
        await surveyApi.create(formData);
        showAlert(
          '<i class="bi bi-check-circle-fill me-2"></i><strong>Success!</strong> Your survey has been submitted successfully. Thank you for your feedback!',
          'success'
        );
      }
      resetForm();
    } catch (err) {
      showAlert(
        `<i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Error!</strong> ${(err as Error).message}`,
        'danger'
      );
    } finally {
      setLoading(false);
    }
  };

  // ── Reset / Edit / Delete ────────────────────────────────────────────────

  const resetForm = () => {
    setFormData(EMPTY_FORM);
    setEditingId(null);
    setRaffleError('');
  };

  const handleEdit = (survey: Survey) => {
    const { id, ...data } = survey;
    setEditingId(id);
    setFormData(data);
    setView('form');
    clearAlert();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this survey?')) return;
    try {
      await surveyApi.remove(id);
      setSurveys((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      showAlert(`Failed to delete survey: ${(err as Error).message}`, 'danger');
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="survey-container">
      {/* Tab Toggle */}
      <div className="d-flex gap-2 mb-3">
        <button
          className={`btn ${view === 'form' ? 'btn-teal' : 'btn-outline-secondary'}`}
          onClick={() => { setView('form'); clearAlert(); }}
        >
          <i className="bi bi-pencil-square me-2"></i>
          {editingId !== null ? 'Edit Survey' : 'Submit Survey'}
        </button>
        <button
          className={`btn ${view === 'list' ? 'btn-teal' : 'btn-outline-secondary'}`}
          onClick={() => { setView('list'); clearAlert(); }}
        >
          <i className="bi bi-table me-2"></i>All Surveys
        </button>
      </div>

      {/* ── FORM VIEW ── */}
      {view === 'form' && (
        <div className="survey-card">
          <div className="survey-header">
            <h2>
              <i className="bi bi-mortarboard-fill me-2"></i>
              {editingId !== null ? 'Edit Survey' : 'Student Survey Form'}
            </h2>
            <p>Help us improve by sharing your feedback about our campus</p>
          </div>

          <div className="survey-body">
            {/* Alert */}
            {alert.type && (
              <div
                className={`alert alert-${alert.type} mb-4`}
                role="alert"
                dangerouslySetInnerHTML={{ __html: alert.message }}
              />
            )}

            <form onSubmit={handleSubmit} noValidate>
              {/* Personal Information */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-person-fill"></i>Personal Information
                </h5>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label htmlFor="firstName" className="form-label">
                      First Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="firstName"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleTextChange}
                      required
                      placeholder="Enter your first name"
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="lastName" className="form-label">
                      Last Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="lastName"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleTextChange}
                      required
                      placeholder="Enter your last name"
                    />
                  </div>
                  <div className="col-12">
                    <label htmlFor="streetAddress" className="form-label">
                      Street Address <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="streetAddress"
                      name="streetAddress"
                      value={formData.streetAddress}
                      onChange={handleTextChange}
                      required
                      placeholder="Enter your street address"
                    />
                  </div>
                  <div className="col-md-5">
                    <label htmlFor="city" className="form-label">
                      City <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="city"
                      name="city"
                      value={formData.city}
                      onChange={handleTextChange}
                      required
                      placeholder="City"
                    />
                  </div>
                  <div className="col-md-4">
                    <label htmlFor="state" className="form-label">
                      State <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="state"
                      name="state"
                      value={formData.state}
                      onChange={handleTextChange}
                      required
                      placeholder="State"
                    />
                  </div>
                  <div className="col-md-3">
                    <label htmlFor="zip" className="form-label">
                      Zip Code <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="zip"
                      name="zip"
                      value={formData.zip}
                      onChange={handleTextChange}
                      required
                      placeholder="Zip"
                      pattern="[0-9]{5}"
                      title="Please enter a valid 5-digit zip code"
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="telephone" className="form-label">
                      Telephone Number <span className="required">*</span>
                    </label>
                    <input
                      type="tel"
                      className="form-control"
                      id="telephone"
                      name="telephone"
                      value={formData.telephone}
                      onChange={handleTextChange}
                      required
                      placeholder="(123) 456-7890"
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="email" className="form-label">
                      E-mail Address <span className="required">*</span>
                    </label>
                    <input
                      type="email"
                      className="form-control"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleTextChange}
                      required
                      placeholder="your-email@example.com"
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="surveyDate" className="form-label">
                      Date of Survey <span className="required">*</span>
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      id="surveyDate"
                      name="surveyDate"
                      value={formData.surveyDate}
                      onChange={handleTextChange}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Campus Preferences */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-building"></i>What did you like most about the campus?
                </h5>
                <p className="form-text mb-3">Select all that apply:</p>
                <div className="checkbox-grid">
                  {CAMPUS_LIKES_OPTIONS.map((opt) => (
                    <div className="checkbox-item" key={opt.value}>
                      <input
                        className="form-check-input"
                        type="checkbox"
                        value={opt.value}
                        id={`like_${opt.value}`}
                        name="campusLikes"
                        checked={formData.campusLikes.includes(opt.value)}
                        onChange={handleCheckboxChange}
                      />
                      <label className="form-check-label" htmlFor={`like_${opt.value}`}>
                        <i className={`bi ${opt.icon} me-1`}></i>
                        {opt.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* How did you hear */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-megaphone"></i>How did you become interested in the university?
                </h5>
                <div className="radio-group">
                  {INTEREST_SOURCE_OPTIONS.map((opt) => (
                    <div className="radio-item" key={opt.value}>
                      <input
                        className="form-check-input"
                        type="radio"
                        name="interestSource"
                        id={`source_${opt.value}`}
                        value={opt.value}
                        checked={formData.interestSource === opt.value}
                        onChange={handleTextChange}
                      />
                      <label className="form-check-label" htmlFor={`source_${opt.value}`}>
                        <i className={`bi ${opt.icon} me-1`}></i>
                        {opt.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommendation */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-star"></i>Likelihood of Recommendation
                </h5>
                <div className="row">
                  <div className="col-md-6">
                    <label htmlFor="recommendation" className="form-label">
                      How likely are you to recommend this school to other prospective students?
                    </label>
                    <select
                      className="form-select"
                      id="recommendation"
                      name="recommendation"
                      value={formData.recommendation}
                      onChange={handleTextChange}
                    >
                      <option value="">-- Select an option --</option>
                      <option value="veryLikely">Very Likely</option>
                      <option value="likely">Likely</option>
                      <option value="unlikely">Unlikely</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Raffle */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-ticket-perforated"></i>Raffle Entry
                </h5>
                <div className="row">
                  <div className="col-12">
                    <label htmlFor="raffle" className="form-label">
                      Enter Your Raffle Numbers
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="raffle"
                      name="raffle"
                      value={formData.raffle ?? ''}
                      onChange={handleTextChange}
                      onBlur={(e) => validateRaffle(e.target.value)}
                      placeholder="e.g., 5, 12, 23, 34, 45, 56, 67, 78, 89, 99"
                    />
                    <div className="form-text mt-2">
                      <i className="bi bi-info-circle me-1"></i>
                      Enter at least 10 comma-separated numbers between 1 and 100. Winners will
                      receive a free movie ticket!
                    </div>
                    {raffleError && (
                      <div className="text-danger mt-2">{raffleError}</div>
                    )}
                  </div>
                </div>
              </div>

              {/* Comments */}
              <div className="form-section">
                <h5 className="section-title">
                  <i className="bi bi-chat-left-text"></i>Additional Comments
                </h5>
                <div className="row">
                  <div className="col-12">
                    <label htmlFor="comments" className="form-label">
                      Share your thoughts, suggestions, or feedback
                    </label>
                    <textarea
                      className="form-control"
                      id="comments"
                      name="comments"
                      rows={5}
                      value={formData.comments ?? ''}
                      onChange={handleTextChange}
                      placeholder="Enter any additional comments here..."
                    />
                  </div>
                </div>
              </div>

              {/* Buttons */}
              <div className="d-flex justify-content-end gap-3 mt-4 pt-3">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={resetForm}
                  disabled={loading}
                >
                  <i className="bi bi-x-circle me-2"></i>Cancel
                </button>
                <button type="submit" className="btn btn-teal" disabled={loading}>
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-send me-2"></i>
                      {editingId !== null ? 'Update Survey' : 'Submit Survey'}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── LIST VIEW ── */}
      {view === 'list' && (
        <div className="survey-card">
          <div className="survey-header">
            <h2>
              <i className="bi bi-table me-2"></i>All Survey Responses
            </h2>
            <p>View, edit, or delete survey submissions</p>
          </div>

          <div className="survey-body">
            {alert.type && (
              <div
                className={`alert alert-${alert.type} mb-4`}
                role="alert"
                dangerouslySetInnerHTML={{ __html: alert.message }}
              />
            )}

            {listLoading ? (
              <div className="text-center py-5">
                <span className="spinner-border" role="status" />
                <p className="mt-3 text-muted">Loading surveys...</p>
              </div>
            ) : surveys.length === 0 ? (
              <div className="text-center py-5 text-muted">
                <i className="bi bi-inbox fs-1 d-block mb-3"></i>
                No survey responses yet. Be the first to submit!
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">
                  <thead className="table-light">
                    <tr>
                      <th>#</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>City, State</th>
                      <th>Survey Date</th>
                      <th>Recommendation</th>
                      <th className="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {surveys.map((survey) => (
                      <tr key={survey.id}>
                        <td>{survey.id}</td>
                        <td>
                          <strong>
                            {survey.firstName} {survey.lastName}
                          </strong>
                        </td>
                        <td>{survey.email}</td>
                        <td>
                          {survey.city}, {survey.state}
                        </td>
                        <td>{survey.surveyDate}</td>
                        <td>
                          <span
                            className={`badge ${
                              survey.recommendation === 'veryLikely'
                                ? 'bg-success'
                                : survey.recommendation === 'likely'
                                ? 'bg-info'
                                : 'bg-secondary'
                            }`}
                          >
                            {survey.recommendation === 'veryLikely'
                              ? 'Very Likely'
                              : survey.recommendation === 'likely'
                              ? 'Likely'
                              : survey.recommendation === 'unlikely'
                              ? 'Unlikely'
                              : '—'}
                          </span>
                        </td>
                        <td className="text-end">
                          <div className="d-flex gap-2 justify-content-end">
                            <button
                              className="btn btn-sm btn-outline-secondary"
                              onClick={() => handleEdit(survey)}
                              title="Edit"
                            >
                              <i className="bi bi-pencil"></i>
                            </button>
                            <button
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => handleDelete(survey.id)}
                              title="Delete"
                            >
                              <i className="bi bi-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="page-footer">
        <p className="mb-0">© 2026 George Mason University Student Survey</p>
      </footer>
    </div>
  );
};

export default SurveyComponent;
