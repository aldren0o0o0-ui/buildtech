import React from 'react';

export const CoolingSpecificationForm = ({ values, onChange, disabled }) => {
  const socketOptions = ['AM5', 'AM4', 'LGA1700', 'LGA1200', 'LGA1151', 'TR4'];
  const currentSockets = Array.isArray(values.supported_sockets)
    ? values.supported_sockets
    : [];

  const handleSocketToggle = (socket) => {
    const next = currentSockets.includes(socket)
      ? currentSockets.filter((s) => s !== socket)
      : [...currentSockets, socket];

    onChange({
      target: {
        name: 'supported_sockets',
        value: next,
      },
    });
  };

  return (
    <div className="spec-form-grid">
      <div className="form-group">
        <label htmlFor="cooling-type" className="form-label">Cooler Type *</label>
        <select
          id="cooling-type"
          name="cooler_type"
          className="form-input"
          value={values.cooler_type || 'AIR'}
          onChange={onChange}
          required
          disabled={disabled}
        >
          <option value="AIR">Air Cooler</option>
          <option value="AIO">AIO Liquid Cooler</option>
          <option value="CUSTOM_LIQUID">Custom Liquid Loop</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="cooling-height" className="form-label">Cooler/Pump Height (mm) *</label>
        <input
          id="cooling-height"
          type="number"
          min="1"
          name="height_mm"
          className="form-input"
          placeholder="e.g. 158, 160"
          value={values.height_mm ?? ''}
          onChange={onChange}
          required
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cooling-rad" className="form-label">Radiator Size (mm, if Liquid)</label>
        <input
          id="cooling-rad"
          type="number"
          min="1"
          name="radiator_size_mm"
          className="form-input"
          placeholder="e.g. 240, 280, 360"
          value={values.radiator_size_mm ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cooling-fan" className="form-label">Fan Size (mm)</label>
        <input
          id="cooling-fan"
          type="number"
          min="1"
          name="fan_size_mm"
          className="form-input"
          placeholder="e.g. 120, 140"
          value={values.fan_size_mm ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group">
        <label htmlFor="cooling-tdp" className="form-label">Max TDP Dissipation (Watts)</label>
        <input
          id="cooling-tdp"
          type="number"
          min="1"
          name="max_tdp_watts"
          className="form-input"
          placeholder="e.g. 250"
          value={values.max_tdp_watts ?? ''}
          onChange={onChange}
          disabled={disabled}
        />
      </div>

      <div className="form-group" style={{ gridColumn: '1 / -1' }}>
        <label className="form-label">Supported Sockets *</label>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
          {socketOptions.map((sock) => (
            <label key={sock} className="form-checkbox-label">
              <input
                type="checkbox"
                className="form-checkbox"
                checked={currentSockets.includes(sock)}
                onChange={() => handleSocketToggle(sock)}
                disabled={disabled}
              />
              {sock}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CoolingSpecificationForm;
