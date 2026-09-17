import React, { useState, useEffect, useCallback, useId } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import productService from '../../products/services/productService';
import compatibilityService from '../services/compatibilityService';

const COMPONENT_SLOTS = [
  { key: 'cpu', label: 'Processor (CPU)', categorySlug: 'cpu' },
  { key: 'motherboard', label: 'Motherboard', categorySlug: 'motherboard' },
  { key: 'memory', label: 'Memory (RAM)', categorySlug: 'memory' },
  { key: 'gpu', label: 'Graphics Card (GPU)', categorySlug: 'gpu' },
  { key: 'psu', label: 'Power Supply (PSU)', categorySlug: 'psu' },
  { key: 'case', label: 'PC Case', categorySlug: 'case' },
  { key: 'storage', label: 'Storage Drive (SSD)', categorySlug: 'storage' },
  { key: 'cooling', label: 'CPU Cooler', categorySlug: 'cooling' },
];

export const CompatibilityCheckerPage = () => {
  const [searchParams] = useSearchParams();
  const preSelectedId = searchParams.get('productId');

  const [availableProducts, setAvailableProducts] = useState({});
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [selectedComponents, setSelectedComponents] = useState({});
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');
  const cpuSelectId = useId();

  // Load active products from catalog
  useEffect(() => {
    let isMounted = true;
    const loadProducts = async () => {
      setLoadingProducts(true);
      try {
        const response = await productService.listProducts();
        const items = Array.isArray(response) ? response : response.items || [];

        // Group by category slug or hardware type
        const grouped = {
          cpu: [],
          motherboard: [],
          memory: [],
          gpu: [],
          psu: [],
          case: [],
          storage: [],
          cooling: [],
        };

        items.forEach((p) => {
          const catSlug = (p.category?.slug || '').toLowerCase();
          const catName = (p.category?.name || '').toLowerCase();

          if (catSlug.includes('cpu') || catName.includes('processor')) {
            grouped.cpu.push(p);
          } else if (catSlug.includes('motherboard') || catName.includes('mainboard')) {
            grouped.motherboard.push(p);
          } else if (catSlug.includes('memory') || catSlug.includes('ram') || catName.includes('memory')) {
            grouped.memory.push(p);
          } else if (catSlug.includes('gpu') || catSlug.includes('graphic') || catName.includes('graphics')) {
            grouped.gpu.push(p);
          } else if (catSlug.includes('psu') || catSlug.includes('power') || catName.includes('power supply')) {
            grouped.psu.push(p);
          } else if (catSlug.includes('case') || catSlug.includes('chassis') || catName.includes('case')) {
            grouped.case.push(p);
          } else if (catSlug.includes('storage') || catSlug.includes('ssd') || catName.includes('storage')) {
            grouped.storage.push(p);
          } else if (catSlug.includes('cool') || catName.includes('cooler')) {
            grouped.cooling.push(p);
          }
        });

        if (isMounted) {
          setAvailableProducts(grouped);

          // Handle pre-selected product
          if (preSelectedId) {
            const targetId = parseInt(preSelectedId, 10);
            const found = items.find((p) => p.id === targetId);
            if (found) {
              for (const [slotKey, prods] of Object.entries(grouped)) {
                if (prods.some((p) => p.id === targetId)) {
                  setSelectedComponents((prev) => ({ ...prev, [slotKey]: found }));
                  break;
                }
              }
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to load catalog products.');
        }
      } finally {
        if (isMounted) {
          setLoadingProducts(false);
        }
      }
    };

    loadProducts();
    return () => {
      isMounted = false;
    };
  }, [preSelectedId]);

  const handleSelect = (slotKey, productIdStr) => {
    if (!productIdStr) {
      handleRemove(slotKey);
      return;
    }
    const productId = parseInt(productIdStr, 10);
    const prod = (availableProducts[slotKey] || []).find((p) => p.id === productId);
    if (prod) {
      setSelectedComponents((prev) => ({ ...prev, [slotKey]: prod }));
      setResult(null);
      setError('');
    }
  };

  const handleRemove = (slotKey) => {
    setSelectedComponents((prev) => {
      const next = { ...prev };
      delete next[slotKey];
      return next;
    });
    setResult(null);
  };

  const handleReset = () => {
    setSelectedComponents({});
    setResult(null);
    setError('');
  };

  const runCompatibilityCheck = useCallback(async () => {
    const selectedList = Object.values(selectedComponents).filter(Boolean);
    if (selectedList.length === 0) {
      setError('Please select at least one hardware component.');
      return;
    }

    setChecking(true);
    setError('');
    try {
      const productIds = selectedList.map((p) => p.id);
      const data = await compatibilityService.checkCompatibility(productIds);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to evaluate compatibility. Please try again.');
    } finally {
      setChecking(false);
    }
  }, [selectedComponents]);

  const selectedCount = Object.values(selectedComponents).filter(Boolean).length;

  return (
    <div className="container" style={{ padding: 'var(--space-8) var(--space-4)' }}>
      {/* Breadcrumb Navigation */}
      <div style={{ display: 'flex', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-4)' }}>
        <Link to="/" style={{ color: 'var(--color-text-secondary)', textDecoration: 'none' }}>Home</Link>
        <span>/</span>
        <span style={{ color: 'var(--color-text)' }}>Compatibility Engine</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h1 style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text)', margin: '0 0 var(--space-2) 0' }}>
          Hardware Compatibility Engine
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: 'var(--font-size-base)', maxWidth: '720px' }}>
          Verify physical and electrical compatibility across selected computer hardware components using BuildTech&apos;s authoritative, deterministic domain rules.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            padding: 'var(--space-4)',
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger-border)',
            color: 'var(--color-danger-text)',
            borderRadius: 'var(--radius-sm)',
            marginBottom: 'var(--space-6)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {error}
        </div>
      )}

      {/* Main Grid: Selectors + Results */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-8)',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Component Selectors */}
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: 'var(--space-6)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
            <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', margin: 0, color: 'var(--color-text)' }}>
              Component Selection ({selectedCount})
            </h2>
            {selectedCount > 0 && (
              <button
                type="button"
                onClick={handleReset}
                className="btn btn-secondary"
                style={{ padding: 'var(--space-1) var(--space-3)', fontSize: 'var(--font-size-xs)' }}
              >
                Reset All
              </button>
            )}
          </div>

          {loadingProducts ? (
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
              Loading hardware components...
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {COMPONENT_SLOTS.map((slot) => {
                const selected = selectedComponents[slot.key];
                const available = availableProducts[slot.key] || [];

                return (
                  <div
                    key={slot.key}
                    style={{
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: 'var(--space-3)',
                      backgroundColor: selected ? 'var(--color-surface-muted)' : 'transparent',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-1)' }}>
                      <label
                        htmlFor={slot.key === 'cpu' ? cpuSelectId : `slot-select-${slot.key}`}
                        style={{
                          fontSize: 'var(--font-size-xs)',
                          fontWeight: 'var(--font-weight-semibold)',
                          color: 'var(--color-text-secondary)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                        }}
                      >
                        {slot.label}
                      </label>
                      {selected && (
                        <button
                          type="button"
                          onClick={() => handleRemove(slot.key)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--color-text-muted)',
                            fontSize: 'var(--font-size-xs)',
                            cursor: 'pointer',
                            padding: '0 var(--space-1)',
                          }}
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    {selected ? (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text)', fontSize: 'var(--font-size-sm)' }}>
                            {selected.name}
                          </div>
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                            SKU: {selected.sku} &bull; ${parseFloat(selected.price).toFixed(2)}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <select
                        id={slot.key === 'cpu' ? cpuSelectId : `slot-select-${slot.key}`}
                        value=""
                        onChange={(e) => handleSelect(slot.key, e.target.value)}
                        className="form-input"
                        style={{ width: '100%', fontSize: 'var(--font-size-sm)', padding: 'var(--space-2)' }}
                      >
                        <option value="">Select {slot.label} ({available.length} available)</option>
                        {available.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} — ${parseFloat(p.price).toFixed(2)}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                );
              })}

              <div style={{ marginTop: 'var(--space-4)' }}>
                <button
                  type="button"
                  id="check-compatibility-btn"
                  onClick={runCompatibilityCheck}
                  disabled={checking || selectedCount === 0}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: 'var(--space-3)', fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)' }}
                >
                  {checking ? 'Evaluating Compatibility...' : `Check Compatibility (${selectedCount} selected)`}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Compatibility Results Breakdown */}
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: 'var(--space-6)',
          }}
        >
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', margin: '0 0 var(--space-4) 0', color: 'var(--color-text)' }}>
            Compatibility Analysis
          </h2>

          {!result && !checking && (
            <div style={{ padding: 'var(--space-12) var(--space-4)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
              <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-2)' }}>
                No active compatibility evaluation
              </div>
              <p style={{ fontSize: 'var(--font-size-sm)', margin: 0, maxWidth: '360px', marginInline: 'auto' }}>
                Select components from the catalog and click &ldquo;Check Compatibility&rdquo; to evaluate sockets, clearances, memory speeds, and power requirements.
              </p>
            </div>
          )}

          {checking && (
            <div style={{ padding: 'var(--space-12) var(--space-4)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
              <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-medium)' }}>
                Evaluating deterministic domain rules...
              </div>
            </div>
          )}

          {result && (
            <div>
              {/* Overall Status Banner */}
              <div
                style={{
                  padding: 'var(--space-4)',
                  borderRadius: 'var(--radius-sm)',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  marginBottom: 'var(--space-6)',
                  backgroundColor:
                    result.status === 'PASS'
                      ? 'var(--color-success-bg)'
                      : result.status === 'WARNING'
                      ? 'var(--color-warning-bg)'
                      : 'var(--color-danger-bg)',
                  borderColor:
                    result.status === 'PASS'
                      ? 'var(--color-success-border)'
                      : result.status === 'WARNING'
                      ? 'var(--color-warning-border)'
                      : 'var(--color-danger-border)',
                  color:
                    result.status === 'PASS'
                      ? 'var(--color-success-text)'
                      : result.status === 'WARNING'
                      ? 'var(--color-warning-text)'
                      : 'var(--color-danger-text)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                  <span style={{ fontWeight: 'var(--font-weight-bold)', fontSize: 'var(--font-size-base)' }}>
                    [{result.status}]
                  </span>
                  <span style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-base)' }}>
                    {result.status === 'PASS'
                      ? 'Compatible Configuration'
                      : result.status === 'WARNING'
                      ? 'Configuration Review Recommended'
                      : 'Incompatible Configuration'}
                  </span>
                </div>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>
                  {result.summary}
                </div>
              </div>

              {/* Power Analysis Card */}
              {result.estimated_system_power_watts !== null && (
                <div
                  style={{
                    backgroundColor: 'var(--color-surface-muted)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: 'var(--space-4)',
                    marginBottom: 'var(--space-6)',
                  }}
                >
                  <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                    System Power Estimates
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                    <div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Estimated Draw</div>
                      <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text)' }}>
                        {result.estimated_system_power_watts} W
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Recommended PSU</div>
                      <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text)' }}>
                        &ge; {result.required_psu_watts} W
                      </div>
                    </div>
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-2)' }}>
                    Calculation includes CPU TDP + GPU TDP + 75W base allowance with 25% safety margin.
                  </div>
                </div>
              )}

              {/* Individual Rules Breakdown */}
              <div style={{ marginBottom: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
                  <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>
                    Rule Verification Details ({result.checks.length})
                  </h3>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    {result.pass_count} Pass &bull; {result.warning_count} Warning &bull; {result.fail_count} Fail
                  </div>
                </div>

                {result.checks.length === 0 ? (
                  <div style={{ padding: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                    No rule combinations applicable to the selected components.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                    {result.checks.map((chk, idx) => {
                      const isPass = chk.status === 'PASS';
                      const isWarn = chk.status === 'WARNING';

                      const statusBg = isPass
                        ? 'var(--color-success-bg)'
                        : isWarn
                        ? 'var(--color-warning-bg)'
                        : 'var(--color-danger-bg)';
                      const statusBorder = isPass
                        ? 'var(--color-success-border)'
                        : isWarn
                        ? 'var(--color-warning-border)'
                        : 'var(--color-danger-border)';
                      const statusText = isPass
                        ? 'var(--color-success-text)'
                        : isWarn
                        ? 'var(--color-warning-text)'
                        : 'var(--color-danger-text)';

                      return (
                        <div
                          key={idx}
                          style={{
                            border: '1px solid var(--color-border)',
                            borderRadius: 'var(--radius-sm)',
                            padding: 'var(--space-3)',
                            backgroundColor: 'var(--color-surface)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-1)' }}>
                            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text)' }}>
                              {chk.rule.replace(/_/g, ' ')}
                            </span>
                            <span
                              style={{
                                fontSize: 'var(--font-size-xs)',
                                fontWeight: 'var(--font-weight-semibold)',
                                padding: '2px 8px',
                                borderRadius: 'var(--radius-sm)',
                                backgroundColor: statusBg,
                                border: `1px solid ${statusBorder}`,
                                color: statusText,
                              }}
                            >
                              {chk.status}
                            </span>
                          </div>
                          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: '1.4' }}>
                            {chk.message}
                          </div>
                          {(chk.actual !== null || chk.expected !== null) && (
                            <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-2)' }}>
                              {chk.actual !== null && <span>Actual: <strong>{String(chk.actual)}</strong></span>}
                              {chk.expected !== null && <span>Expected: <strong>{String(chk.expected)}</strong></span>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompatibilityCheckerPage;
