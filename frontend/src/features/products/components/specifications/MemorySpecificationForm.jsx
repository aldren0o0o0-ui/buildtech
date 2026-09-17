import React from 'react';

export const MemorySpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="ram-type" className="form-label">Memory Type *</label>
        <input
          id="ram-type"
          type="text"
          name="memory_type"
          className="form-input"
          placeholder="e.g. DDR5, DDR4"
          value={values.memory_type || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="ram-cap" className="form-label">Total Capacity (GB) *</label>
        <input
          id="ram-cap"
          type="number"
          min="1"
          name="capacity_gb"
          className="form-input"
          placeholder="e.g. 32"
          value={values.capacity_gb ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="ram-speed" className="form-label">Speed (MHz) *</label>
        <input
          id="ram-speed"
          type="number"
          min="1"
          name="speed_mhz"
          className="form-input"
          placeholder="e.g. 6000"
          value={values.speed_mhz ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="ram-modules" className="form-label">Module Count *</label>
        <input
          id="ram-modules"
          type="number"
          min="1"
          name="module_count"
          className="form-input"
          placeholder="e.g. 2 (for 2x16GB)"
          value={values.module_count ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="ram-cas" className="form-label">CAS Latency (CL)</label>
        <input
          id="ram-cas"
          type="number"
          min="1"
          name="cas_latency"
          className="form-input"
          placeholder="e.g. 30, 36"
          value={values.cas_latency ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default MemorySpecificationForm;
