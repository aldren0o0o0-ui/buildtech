import React from 'react';

export const StorageSpecificationForm = ({ values, onChange, disabled }) => {
  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="storage-type" className="form-label">Storage Type *</label>
        <select
          id="storage-type"
          name="storage_type"
          className="form-input"
          value={values.storage_type || 'SSD'}
          onChange={onChange}
          required
          disabled={disabled}
        >
          <option value="SSD">SSD (Solid State Drive)</option>
          <option value="HDD">HDD (Mechanical Hard Drive)</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="storage-cap" className="form-label">Capacity (GB) *</label>
        <input
          id="storage-cap"
          type="number"
          min="1"
          name="capacity_gb"
          className="form-input"
          placeholder="e.g. 1000 for 1TB, 2000 for 2TB"
          value={values.capacity_gb ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="storage-interface" className="form-label">Interface *</label>
        <input
          id="storage-interface"
          type="text"
          name="interface"
          className="form-input"
          placeholder="e.g. PCIe 4.0 NVMe, SATA III"
          value={values.interface || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="storage-form-factor" className="form-label">Form Factor *</label>
        <input
          id="storage-form-factor"
          type="text"
          name="form_factor"
          className="form-input"
          placeholder="e.g. M.2 2280, 2.5 inch, 3.5 inch"
          value={values.form_factor || ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="storage-read" className="form-label">Read Speed (MB/s)</label>
        <input
          id="storage-read"
          type="number"
          min="0"
          name="read_speed_mbps"
          className="form-input"
          placeholder="e.g. 7450"
          value={values.read_speed_mbps ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="storage-write" className="form-label">Write Speed (MB/s)</label>
        <input
          id="storage-write"
          type="number"
          min="0"
          name="write_speed_mbps"
          className="form-input"
          placeholder="e.g. 6900"
          value={values.write_speed_mbps ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default StorageSpecificationForm;
