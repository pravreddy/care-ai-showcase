/**
 * apiServices.test.js — Validates all service objects export expected methods.
 */
import {
  authService, documentService, signingService,
  salesService, organisationService, paymentService, templateService,
} from '../services/api';

describe('authService', () => {
  const methods = ['register', 'login', 'logout', 'getProfile', 'getDashboard', 'changePassword', 'forgotPassword', 'getOAuthProviders', 'resendActivation'];
  test.each(methods)('has %s method', (m) => { expect(typeof authService[m]).toBe('function'); });
});

describe('documentService', () => {
  const methods = ['list', 'get', 'upload', 'sendForSigning', 'auditLog', 'delete', 'download', 'getFields', 'saveFields'];
  test.each(methods)('has %s method', (m) => { expect(typeof documentService[m]).toBe('function'); });
  test('getPdfUrl returns string with id', () => {
    const url = documentService.getPdfUrl('test-id');
    expect(url).toContain('test-id');
    expect(url).toContain('/pdf/');
  });
});

describe('signingService', () => {
  const methods = ['getDocument', 'sign'];
  test.each(methods)('has %s method', (m) => { expect(typeof signingService[m]).toBe('function'); });
  test('getPdfUrl returns string with token', () => {
    const url = signingService.getPdfUrl('abc123');
    expect(url).toContain('abc123');
  });
});

describe('salesService', () => {
  const methods = ['getClients', 'getClient', 'createClient', 'updateClient', 'deleteClient', 'getDailySales', 'createDailySale', 'updateDailySale', 'bulkCreateSales', 'getSummary', 'getInvoices', 'generateInvoice', 'downloadInvoice', 'sendInvoiceEmail', 'markInvoicePaid'];
  test.each(methods)('has %s method', (m) => { expect(typeof salesService[m]).toBe('function'); });
});

describe('organisationService', () => {
  const methods = ['list', 'get', 'create', 'update', 'getMembers', 'getMyOrganisations', 'createMember', 'inviteMember', 'getInvitations', 'acceptInvitation'];
  test.each(methods)('has %s method', (m) => { expect(typeof organisationService[m]).toBe('function'); });
});

describe('paymentService', () => {
  const methods = ['getPlans', 'getProviders', 'checkout', 'getStatus'];
  test.each(methods)('has %s method', (m) => { expect(typeof paymentService[m]).toBe('function'); });
});

describe('templateService', () => {
  const methods = ['list', 'useTemplate', 'get', 'saveFromDocument', 'delete'];
  test.each(methods)('has %s method', (m) => { expect(typeof templateService[m]).toBe('function'); });
});
