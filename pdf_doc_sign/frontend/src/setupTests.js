import '@testing-library/jest-dom';
import 'jest-canvas-mock';

// Global URL mocks needed for PDF download tests
global.URL.createObjectURL = jest.fn(() => 'blob:mock');
global.URL.revokeObjectURL = jest.fn();
