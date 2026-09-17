import React from 'react';

export const CaseSpecificationForm = ({ values, onChange, disabled }) => {
  const formFactorOptions = ['E-ATX', 'ATX', 'Micro-ATX', 'Mini-ITX'];
  const currentFactors = Array.isArray(values.supported_motherboard_form_factors)
    ? values.supported_motherboard_form_factors
    : [];

  const handleCheckboxToggle = (factor) => {
    const next = currentFactors.includes(factor)
      ? currentFactors.filter((f) => f !== factor)
      : [...currentFactors, factor];

    onChange({
      target: {
        name: 'supported_motherboard_form_factors',
        value: next,
      },
    });
  };

  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="case-type" className="form-label">Case Type / Size *</label>
        <input
          id="case-type"
          type="text"
          name="case_type"
          className="form-input"
          placeholder="e.g. Mid Tower, Full Tower, Small Form Factor"
          value={values.case_type || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="case-psu-ff" className="form-label">PSU Form Factor *</label>
        <input
          id="case-psu-ff"
          type="text"
          name="psu_form_factor"
          className="form-input"
          placeholder="e.g. ATX, SFX"
          value={values.psu_form_factor || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="case-max-gpu" className="form-label">Max GPU Length (mm) *</label>
        <input
          id="case-max-gpu"
          type="number"
          min="1"
          name="max_gpu_length_mm"
          className="form-input"
          placeholder="e.g. 360, 400"
          value={values.max_gpu_length_mm ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="case-max-cooler" className="form-label">Max CPU Cooler Height (mm) *</label>
        <input
          id="case-max-cooler"
          type="number"
          min="1"
          name="max_cpu_cooler_height_mm"
          className="form-input"
          placeholder="e.g. 170"
          value={values.max_cpu_cooler_height_mm ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group" style={{ gridColumn: '1 / -1' }}>
        <label className="form-label">Supported Motherboard Form Factors *</label>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
          {formFactorOptions.map((factor) => (
            <label key={factor} className="form-checkbox-label">
              <input
                type="checkbox"
                className="form-checkbox"
                checked={currentFactors.includes(factor)}
                onChange={() => handleCheckboxToggle(factor)}
                disabled={disabled}
              />
              {factor}
            </label>
          ))}
        </div>
      </div>

      <div className="form-group" style={{ gridColumn: '1 / -1' }}>
        <label htmlFor="case-bays" className="form-label">Drive Bays</label>
        <input
          id="case-bays"
          type="text"
          name="drive_bays"
          className="form-input"
          placeholder="e.g. 2x 3.5 inch, 2x 2.5 inch"
          value={values.drive_bays || ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default CaseSpecificationForm;
