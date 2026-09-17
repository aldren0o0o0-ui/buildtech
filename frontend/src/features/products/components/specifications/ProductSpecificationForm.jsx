import React from 'react';
import CpuSpecificationForm from './CpuSpecificationForm';
import GpuSpecificationForm from './GpuSpecificationForm';
import MotherboardSpecificationForm from './MotherboardSpecificationForm';
import MemorySpecificationForm from './MemorySpecificationForm';
import StorageSpecificationForm from './StorageSpecificationForm';
import PsuSpecificationForm from './PsuSpecificationForm';
import CaseSpecificationForm from './CaseSpecificationForm';
import CoolingSpecificationForm from './CoolingSpecificationForm';

export const resolveHardwareType = (category) => {
  if (!category) return null;
  const slug = (category.slug || '').toLowerCase();
  const name = (category.name || '').toLowerCase();

  if (slug.includes('cpu') || name.includes('processor') || name.includes('cpu')) return 'CPU';
  if (slug.includes('gpu') || name.includes('graphics') || name.includes('video card')) return 'GPU';
  if (slug.includes('motherboard') || name.includes('motherboard') || name.includes('mainboard')) return 'MOTHERBOARD';
  if (slug.includes('memory') || slug.includes('ram') || name.includes('memory') || name.includes('ram')) return 'MEMORY';
  if (slug.includes('storage') || slug.includes('ssd') || name.includes('storage') || name.includes('drive')) return 'STORAGE';
  if (slug.includes('psu') || slug.includes('power') || name.includes('power supply')) return 'PSU';
  if (slug.includes('case') || slug.includes('chassis') || name.includes('case')) return 'CASE';
  if (slug.includes('cooling') || slug.includes('cooler') || name.includes('cooling') || name.includes('cooler')) return 'COOLING';

  return null;
};

export const ProductSpecificationForm = ({ category, values, onChange, disabled }) => {
  const hwType = resolveHardwareType(category);

  if (!hwType) {
    return (
      <div className="spec-unsupported-notice">
        <p>
          Structured technical hardware specifications are not configured for category{' '}
          <strong>"{category?.name || 'General'}"</strong>.
        </p>
      </div>
    );
  }

  return (
    <div className="spec-form-container">
      <div className="spec-form-header">
        <h4 className="spec-form-title">
          {hwType} Technical Specifications
        </h4>
        <span className="badge badge-subtle">Hardware Category: {hwType}</span>
      </div>

      {hwType === 'CPU' && (
        <CpuSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'GPU' && (
        <GpuSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'MOTHERBOARD' && (
        <MotherboardSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'MEMORY' && (
        <MemorySpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'STORAGE' && (
        <StorageSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'PSU' && (
        <PsuSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'CASE' && (
        <CaseSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
      {hwType === 'COOLING' && (
        <CoolingSpecificationForm values={values} onChange={onChange} disabled={disabled} />
      )}
    </div>
  );
};

export default ProductSpecificationForm;
