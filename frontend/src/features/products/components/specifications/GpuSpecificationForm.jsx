import React from 'react';

export const GpuSpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="gpu-chipset" className="form-label">Chipset *</label>
        <input
          id="gpu-chipset"
          type="text"
          name="chipset"
          className="form-input"
          placeholder="e.g. AD104 / GeForce RTX 4070 Super"
          value={values.chipset || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-vram" className="form-label">VRAM (GB) *</label>
        <input
          id="gpu-vram"
          type="number"
          min="1"
          name="vram_gb"
          className="form-input"
          placeholder="e.g. 12"
          value={values.vram_gb ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-mem-type" className="form-label">Memory Type *</label>
        <input
          id="gpu-mem-type"
          type="text"
          name="memory_type"
          className="form-input"
          placeholder="e.g. GDDR6X, GDDR6"
          value={values.memory_type || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-boost-clock" className="form-label">Boost Clock (MHz) *</label>
        <input
          id="gpu-boost-clock"
          type="number"
          min="0"
          name="boost_clock_mhz"
          className="form-input"
          placeholder="e.g. 2475"
          value={values.boost_clock_mhz ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-core-clock" className="form-label">Base/Core Clock (MHz)</label>
        <input
          id="gpu-core-clock"
          type="number"
          min="0"
          name="core_clock_mhz"
          className="form-input"
          placeholder="e.g. 1980"
          value={values.core_clock_mhz ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-length" className="form-label">Length (mm) *</label>
        <input
          id="gpu-length"
          type="number"
          min="0"
          name="length_mm"
          className="form-input"
          placeholder="e.g. 242"
          value={values.length_mm ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-tdp" className="form-label">TDP (Watts) *</label>
        <input
          id="gpu-tdp"
          type="number"
          min="0"
          name="tdp_watts"
          className="form-input"
          placeholder="e.g. 220"
          value={values.tdp_watts ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="gpu-psu" className="form-label">Recommended PSU (Watts) *</label>
        <input
          id="gpu-psu"
          type="number"
          min="0"
          name="recommended_psu_watts"
          className="form-input"
          placeholder="e.g. 650"
          value={values.recommended_psu_watts ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default GpuSpecificationForm;
