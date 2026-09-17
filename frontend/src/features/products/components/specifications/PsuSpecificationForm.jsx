import React from 'react';

export const PsuSpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="psu-wattage" className="form-label">Wattage (Watts) *</label>
        <input
          id="psu-wattage"
          type="number"
          min="1"
          name="wattage"
          className="form-input"
          placeholder="e.g. 750, 850, 1000"
          value={values.wattage ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="psu-efficiency" className="form-label">Efficiency Rating *</label>
        <input
          id="psu-efficiency"
          type="text"
          name="efficiency_rating"
          className="form-input"
          placeholder="e.g. 80+ Gold, 80+ Platinum, 80+ Bronze"
          value={values.efficiency_rating || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="psu-modularity" className="form-label">Modularity *</label>
        <select
          id="psu-modularity"
          name="modularity"
          className="form-input"
          value={values.modularity || 'Full Modular'}
          onChange={onChange}
          required
          disabled={disabled}
        >
          <option value="Full Modular">Full Modular</option>
          <option value="Semi-Modular">Semi-Modular</option>
          <option value="Non-Modular">Non-Modular</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="psu-form-factor" className="form-label">Form Factor *</label>
        <input
          id="psu-form-factor"
          type="text"
          name="form_factor"
          className="form-input"
          placeholder="e.g. ATX, SFX, SFX-L"
          value={values.form_factor || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default PsuSpecificationForm;
