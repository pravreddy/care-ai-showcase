import SIGNATURE_TABS from '../utils/signatureTabs';

describe('SIGNATURE_TABS configuration', () => {
  test('exports non-empty array', () => { expect(Array.isArray(SIGNATURE_TABS)).toBe(true); expect(SIGNATURE_TABS.length).toBeGreaterThan(0); });
  test('has exactly 3 tabs', () => { expect(SIGNATURE_TABS).toHaveLength(3); });
  test('each tab has required properties', () => {
    SIGNATURE_TABS.forEach((tab) => {
      expect(tab).toHaveProperty('label');
      expect(tab).toHaveProperty('icon');
      expect(tab).toHaveProperty('component');
      expect(tab).toHaveProperty('needsName');
    });
  });
  test('labels are Draw, Type, Upload', () => { expect(SIGNATURE_TABS.map(t => t.label)).toEqual(['Draw', 'Type', 'Upload']); });
  test('only Type needs signerName', () => {
    const needsName = SIGNATURE_TABS.filter(t => t.needsName);
    expect(needsName).toHaveLength(1);
    expect(needsName[0].label).toBe('Type');
  });
  test('all icons are React elements', () => { SIGNATURE_TABS.forEach(tab => { expect(tab.icon).toBeTruthy(); expect(tab.icon.$$typeof).toBeTruthy(); }); });
});
