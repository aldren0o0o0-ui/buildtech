import React from 'react';

export const CpuSpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="cpu-socket" className="form-label">Socket *</label>
        <input
          id="cpu-socket"
          type="text"
          name="socket"
          className="form-input"
          placeholder="e.g. AM5, LGA1700"
          value={values.socket || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-cores" className="form-label">Core Count *</label>
        <input
          id="cpu-cores"
          type="number"
          min="1"
          name="core_count"
          className="form-input"
          placeholder="e.g. 8"
          value={values.core_count ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-threads" className="form-label">Thread Count *</label>
        <input
          id="cpu-threads"
          type="number"
          min="1"
          name="thread_count"
          className="form-input"
          placeholder="e.g. 16"
          value={values.thread_count ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-base-clock" className="form-label">Base Clock (GHz) *</label>
        <input
          id="cpu-base-clock"
          type="number"
          step="0.01"
          min="0"
          name="base_clock_ghz"
          className="form-input"
          placeholder="e.g. 4.20"
          value={values.base_clock_ghz ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-boost-clock" className="form-label">Boost Clock (GHz) *</label>
        <input
          id="cpu-boost-clock"
          type="number"
          step="0.01"
          min="0"
          name="boost_clock_ghz"
          className="form-input"
          placeholder="e.g. 5.00"
          value={values.boost_clock_ghz ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-tdp" className="form-label">TDP (Watts) *</label>
        <input
          id="cpu-tdp"
          type="number"
          min="0"
          name="tdp_watts"
          className="form-input"
          placeholder="e.g. 120"
          value={values.tdp_watts ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-arch" className="form-label">Architecture</label>
        <input
          id="cpu-arch"
          type="text"
          name="architecture"
          className="form-input"
          placeholder="e.g. Zen 4, Raptor Lake"
          value={values.architecture || ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cpu-igpu" className="form-label">Integrated Graphics</label>
        <input
          id="cpu-igpu"
          type="text"
          name="integrated_graphics"
          className="form-input"
          placeholder="e.g. AMD Radeon Graphics, None"
          value={values.integrated_graphics || ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default CpuSpecificationForm;
