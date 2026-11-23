// Provider and release identification shown in the interface.
// The same details are in docs/compliance/ (declaration of conformity,
// instructions for use). Change them together.

export const PROVIDER = {
  name: "Nekod Test Labs B.V.",
  street: "Keizersgracht 100",
  postcodeCity: "1015 CW Amsterdam",
  country: "the Netherlands",
  email: "compliance@nekod-testlabs.example",
} as const;

export const PRODUCT = {
  name: "PatientTriage.ai",
  version: "1.0.0",
  euDatabaseRegistration: "EUDB-HR-2026-0042-PT",
} as const;
