import React from 'react';

export const MotherboardSpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="mb-socket" className="form-label">Socket *</label>
        <input
          id="mb-socket"
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
        <label htmlFor="mb-chipset" className="form-label">Chipset *</label>
        <input
          id="mb-chipset"
          type="text"
          name="chipset"
          className="form-input"
          placeholder="e.g. B650, Z790, X670E"
          value={values.chipset || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="mb-form-factor" className="form-label">Form Factor *</label>
        <input
          id="mb-form-factor"
          type="text"
          name="form_factor"
          className="form-input"
          placeholder="e.g. ATX, Micro-ATX, Mini-ITX"
          value={values.form_factor || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="mb-mem-type" className="form-label">Memory Type *</label>
        <input
          id="mb-mem-type"
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
        <label htmlFor="mb-mem-slots" className="form-label">Memory Slots *</label>
        <input
          id="mb-mem-slots"
          type="number"
          min="1"
          name="memory_slots"
          className="form-input"
          placeholder="e.g. 4"
          value={values.memory_slots ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="mb-max-mem" className="form-label">Max Memory (GB) *</label>
        <input
          id="mb-max-mem"
          type="number"
          min="1"
          name="max_memory_gb"
          className="form-input"
          placeholder="e.g. 192"
          value={values.max_memory_gb ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="mb-pcie" className="form-label">PCIe Version</label>
        <input
          id="mb-pcie"
          type="text"
          name="pcie_version"
          className="form-input"
          placeholder="e.g. PCIe 5.0, PCIe 4.0"
          value={values.pcie_version || ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group" style={{ display: 'flex', alignItems: 'center', paddingTop: '1.75rem' }}>
        <label className="form-checkbox-label">
          <input
            type="checkbox"
            name="wifi"
            className="form-checkbox"
            checked={Boolean(values.wifi)}
            onChange={onChange}
            disabled={disabled}
          />
          Built-in Wi-Fi / Bluetooth
        </label>
      </div>
    </div>
  );
};

export default MotherboardSpecificationForm;
